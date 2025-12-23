"""
QuickBooks Online Integration Service
Handles OAuth, customer sync, and invoice creation
"""

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.detailline import SalesItemLine, SalesItemLineDetail
from quickbooks.objects.item import Item
from datetime import datetime, timedelta
from db import fetch_query, execute_query
import os
from typing import Optional, Dict, List

# QuickBooks OAuth Configuration
QB_REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI", "https://snow-contractor.com/quickbooks/callback")
QB_ENVIRONMENT = os.getenv("QUICKBOOKS_ENVIRONMENT", "production")  # or "sandbox"


class QuickBooksService:
    """Service class for QuickBooks Online API operations"""

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self.auth_client = None
        self.qb_client = None
        self.qb_client_id = None
        self.qb_client_secret = None
        self._load_qb_credentials()
        self._load_credentials()

    def _load_qb_credentials(self):
        """Load QuickBooks Client ID and Secret from api_keys table"""
        # Try environment variables first (fallback)
        self.qb_client_id = os.getenv("QUICKBOOKS_CLIENT_ID", "")
        self.qb_client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET", "")

        # Override with database values if available
        query = """
            SELECT key_name, key_value
            FROM api_keys
            WHERE key_name IN ('quickbooks_client_id', 'quickbooks_client_secret')
            AND user_id IS NULL
        """
        result = fetch_query(query)

        if result:
            for row in result:
                if row['key_name'] == 'quickbooks_client_id' and row['key_value']:
                    self.qb_client_id = row['key_value']
                elif row['key_name'] == 'quickbooks_client_secret' and row['key_value']:
                    self.qb_client_secret = row['key_value']

    def _load_credentials(self):
        """Load stored QuickBooks credentials for this tenant"""
        query = """
            SELECT realm_id, access_token, refresh_token, token_expires_at
            FROM quickbooks_credentials
            WHERE tenant_id = %s
        """
        result = fetch_query(query, (self.tenant_id,))

        if result and len(result) > 0:
            creds = result[0]
            self.realm_id = creds['realm_id']
            self.access_token = creds['access_token']
            self.refresh_token = creds['refresh_token']
            self.token_expires_at = creds['token_expires_at']

            # Check if token needs refresh
            if datetime.now() >= self.token_expires_at - timedelta(minutes=10):
                self._refresh_access_token()

            # Initialize QB client
            self.qb_client = QuickBooks(
                auth_client=self._get_auth_client(),
                refresh_token=self.refresh_token,
                company_id=self.realm_id,
                minorversion=65
            )
        else:
            self.realm_id = None
            self.access_token = None
            self.refresh_token = None

    def _get_auth_client(self):
        """Get Intuit AuthClient instance"""
        if not self.auth_client:
            if not self.qb_client_id or not self.qb_client_secret:
                raise Exception("QuickBooks credentials not configured. Please add Client ID and Secret in API Settings.")

            self.auth_client = AuthClient(
                client_id=self.qb_client_id,
                client_secret=self.qb_client_secret,
                redirect_uri=QB_REDIRECT_URI,
                environment=QB_ENVIRONMENT
            )
        return self.auth_client

    def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        auth_client = self._get_auth_client()
        auth_client.refresh(refresh_token=self.refresh_token)

        self.access_token = auth_client.access_token
        self.refresh_token = auth_client.refresh_token
        self.token_expires_at = datetime.now() + timedelta(seconds=3600)

        # Update in database
        query = """
            UPDATE quickbooks_credentials
            SET access_token = %s,
                refresh_token = %s,
                token_expires_at = %s,
                updated_at = NOW()
            WHERE tenant_id = %s
        """
        execute_query(query, (
            self.access_token,
            self.refresh_token,
            self.token_expires_at,
            self.tenant_id
        ))

    def get_authorization_url(self, state: str = None) -> str:
        """Get QuickBooks OAuth authorization URL"""
        auth_client = self._get_auth_client()
        # Note: intuit-oauth doesn't use state parameter, we'll track tenant via session
        return auth_client.get_authorization_url([Scopes.ACCOUNTING])

    def handle_oauth_callback(self, auth_code: str, realm_id: str):
        """Handle OAuth callback and store credentials"""
        auth_client = self._get_auth_client()
        auth_client.get_bearer_token(auth_code, realm_id=realm_id)

        access_token = auth_client.access_token
        refresh_token = auth_client.refresh_token
        expires_at = datetime.now() + timedelta(seconds=3600)

        # Store or update credentials
        query = """
            INSERT INTO quickbooks_credentials
            (tenant_id, realm_id, access_token, refresh_token, token_expires_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                realm_id = %s,
                access_token = %s,
                refresh_token = %s,
                token_expires_at = %s,
                updated_at = NOW()
        """
        execute_query(query, (
            self.tenant_id, realm_id, access_token, refresh_token, expires_at,
            realm_id, access_token, refresh_token, expires_at
        ))

        # Reload credentials
        self._load_credentials()

    def is_connected(self) -> bool:
        """Check if QuickBooks is connected for this tenant"""
        return self.qb_client is not None

    def sync_property_as_customer(self, property_id: int) -> Optional[str]:
        """
        Sync a property to QuickBooks as a customer
        Returns QuickBooks Customer ID
        """
        if not self.is_connected():
            raise Exception("QuickBooks not connected")

        # Get property details
        query = "SELECT id, name, address FROM locations WHERE id = %s"
        prop = fetch_query(query, (property_id,))[0]

        # Check if already mapped
        mapping_query = "SELECT quickbooks_customer_id FROM quickbooks_customer_mapping WHERE property_id = %s"
        existing = fetch_query(mapping_query, (property_id,))

        if existing:
            return existing[0]['quickbooks_customer_id']

        # Create customer in QuickBooks
        customer = Customer()
        customer.DisplayName = prop['name']
        customer.CompanyName = prop['name']

        # Parse address
        if prop['address']:
            customer.BillAddr = {
                'Line1': prop['address']
            }

        customer.save(qb=self.qb_client)

        # Store mapping
        mapping_insert = """
            INSERT INTO quickbooks_customer_mapping
            (property_id, quickbooks_customer_id, quickbooks_display_name)
            VALUES (%s, %s, %s)
        """
        execute_query(mapping_insert, (property_id, str(customer.Id), customer.DisplayName))

        return str(customer.Id)

    def create_invoice_for_event(self, property_id: int, winter_event_id: int) -> Dict:
        """
        Create QuickBooks invoice for a property's winter event
        Calculates billing based on property billing_type (hourly or per_occurrence)
        """
        if not self.is_connected():
            raise Exception("QuickBooks not connected")

        # Get or create customer
        qb_customer_id = self.sync_property_as_customer(property_id)

        # Get property billing settings
        prop_query = """
            SELECT name, billing_type, plow_rate, salt_rate,
                   sidewalk_deice_rate, sidewalk_snow_rate
            FROM locations WHERE id = %s
        """
        prop = fetch_query(prop_query, (property_id,))[0]

        # Get event details
        event_query = "SELECT event_name, start_time FROM winter_events WHERE id = %s"
        event = fetch_query(event_query, (winter_event_id,))[0]

        # Get logs for this property and event
        logs_query = """
            SELECT
                equipment,
                SUM(TIMESTAMPDIFF(SECOND, time_in, time_out) / 3600) as total_hours,
                COUNT(*) as occurrences
            FROM winter_ops_logs
            WHERE property_id = %s AND winter_event_id = %s
            GROUP BY equipment
        """
        logs = fetch_query(logs_query, (property_id, winter_event_id))

        # Create invoice
        invoice = Invoice()
        invoice.CustomerRef = {"value": qb_customer_id}
        invoice.TxnDate = datetime.now().strftime('%Y-%m-%d')
        invoice.DueDate = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

        # Add line items based on billing type
        line_items = []

        if prop['billing_type'] == 'hourly':
            # Hourly billing - use equipment hours
            for log in logs:
                line = SalesItemLine()
                line.Amount = round(log['total_hours'] * 150, 2)  # $150/hr default
                line.Description = f"{event['event_name']} - {log['equipment']} ({log['total_hours']:.2f} hours)"

                detail = SalesItemLineDetail()
                detail.Qty = log['total_hours']
                detail.UnitPrice = 150
                line.SalesItemLineDetail = detail

                line_items.append(line)

        else:  # per_occurrence
            # Per-occurrence billing - use configured rates
            service_rates = {
                'Plow': prop['plow_rate'],
                'Salt': prop['salt_rate'],
                'Sidewalk De-ice': prop['sidewalk_deice_rate'],
                'Sidewalk Snow': prop['sidewalk_snow_rate']
            }

            for log in logs:
                # Match equipment to service type
                rate = 100  # default
                service_name = log['equipment']

                if 'plow' in log['equipment'].lower():
                    rate = prop['plow_rate'] or 100
                    service_name = 'Plowing'
                elif 'salt' in log['equipment'].lower():
                    rate = prop['salt_rate'] or 75
                    service_name = 'Salting'

                line = SalesItemLine()
                line.Amount = round(log['occurrences'] * rate, 2)
                line.Description = f"{event['event_name']} - {service_name} ({log['occurrences']} occurrences)"

                detail = SalesItemLineDetail()
                detail.Qty = log['occurrences']
                detail.UnitPrice = rate
                line.SalesItemLineDetail = detail

                line_items.append(line)

        invoice.Line = line_items
        invoice.save(qb=self.qb_client)

        # Calculate total
        total_amount = sum(line.Amount for line in line_items)

        # Store invoice record
        invoice_insert = """
            INSERT INTO quickbooks_invoices
            (tenant_id, property_id, winter_event_id, quickbooks_invoice_id,
             quickbooks_invoice_number, total_amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(invoice_insert, (
            self.tenant_id,
            property_id,
            winter_event_id,
            str(invoice.Id),
            invoice.DocNumber,
            total_amount,
            'sent'
        ))

        return {
            'invoice_id': str(invoice.Id),
            'invoice_number': invoice.DocNumber,
            'total_amount': total_amount,
            'customer_name': prop['name'],
            'event_name': event['event_name']
        }

    def disconnect(self):
        """Disconnect QuickBooks integration for this tenant"""
        query = "DELETE FROM quickbooks_credentials WHERE tenant_id = %s"
        execute_query(query, (self.tenant_id,))
