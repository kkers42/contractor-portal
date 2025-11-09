-- MySQL dump 10.13  Distrib 9.2.0, for Win64 (x86_64)
--
-- Host: localhost    Database: contractor_portal
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin_settings`
--

DROP TABLE IF EXISTS `admin_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `setting` varchar(255) DEFAULT NULL,
  `value` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `setting` (`setting`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_settings`
--

LOCK TABLES `admin_settings` WRITE;
/*!40000 ALTER TABLE `admin_settings` DISABLE KEYS */;
INSERT INTO `admin_settings` VALUES (1,'signup_notification_email','contractorappdev@gmail.com');
/*!40000 ALTER TABLE `admin_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `green_services`
--

DROP TABLE IF EXISTS `green_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `green_services` (
  `id` int NOT NULL AUTO_INCREMENT,
  `property_id` int NOT NULL,
  `subcontractor_id` int DEFAULT NULL,
  `service_type` varchar(255) NOT NULL,
  `product_used` int DEFAULT NULL,
  `product_quantity` int DEFAULT '0',
  `service_date` date NOT NULL,
  `time_in` time DEFAULT NULL,
  `time_out` time DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `product_used` (`product_used`),
  CONSTRAINT `green_services_ibfk_1` FOREIGN KEY (`property_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `green_services_ibfk_2` FOREIGN KEY (`product_used`) REFERENCES `landscape_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `green_services`
--

LOCK TABLES `green_services` WRITE;
/*!40000 ALTER TABLE `green_services` DISABLE KEYS */;
/*!40000 ALTER TABLE `green_services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `green_services_logs`
--

DROP TABLE IF EXISTS `green_services_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `green_services_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `property_id` int DEFAULT NULL,
  `subcontractor_name` varchar(255) DEFAULT NULL,
  `time_in` datetime DEFAULT NULL,
  `time_out` datetime DEFAULT NULL,
  `service_type` varchar(100) DEFAULT NULL,
  `products_used` text,
  `quantity_used` decimal(10,2) DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  CONSTRAINT `green_services_logs_ibfk_1` FOREIGN KEY (`property_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `green_services_logs`
--

LOCK TABLES `green_services_logs` WRITE;
/*!40000 ALTER TABLE `green_services_logs` DISABLE KEYS */;
INSERT INTO `green_services_logs` VALUES (1,5,'bubbles','2025-03-11 22:03:00','2025-03-12 11:04:00','Mowing','chemicals ',1.15,'this is awesome ');
/*!40000 ALTER TABLE `green_services_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timesheet_id` int NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `status` enum('Pending','Paid') DEFAULT 'Pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `timesheet_id` (`timesheet_id`),
  CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`timesheet_id`) REFERENCES `timesheets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `landscape_products`
--

DROP TABLE IF EXISTS `landscape_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `landscape_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `unit` varchar(50) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `landscape_products`
--

LOCK TABLES `landscape_products` WRITE;
/*!40000 ALTER TABLE `landscape_products` DISABLE KEYS */;
INSERT INTO `landscape_products` VALUES (1,'','',NULL),(2,'Black Double Cut Mulch','Yards',NULL),(3,'Bag Mulch, Black Double','Bags',NULL),(4,'Topsoil','Yards',NULL),(5,'Weed Barrier','Roll',NULL),(6,'Pre-Emergent','1 lb. Bag',NULL);
/*!40000 ALTER TABLE `landscape_products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `sqft` int DEFAULT NULL,
  `area_manager` varchar(100) DEFAULT NULL,
  `plow` tinyint(1) DEFAULT '0',
  `salt` tinyint(1) DEFAULT '0',
  `notes` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (5,'tested','55 testing ave',10,'bubbles',1,1,NULL),(6,'US Bank Anderson','7350 Beechmont Ave, Cincinnati, OH 45230',0,'N/A',1,1,NULL),(7,'Starbucks Eastgate','816 Eastgate N Dr, Cincinnati, OH 45245',0,'N/A',1,1,NULL),(8,'Eastgate Marketplace','816 Eastgate N Dr, Cincinnati, OH 45245',0,'N/A',1,1,NULL),(9,'US Bank Batavia ','968 Old State Rte 74, Batavia, OH 45103',0,'N/A',1,1,NULL),(10,'McNicholas High School','6534 Beechmont Ave, Cincinnati, OH 45230',0,'N/A',1,1,NULL),(11,'US Bank Mt Washington','2261 Beechmont Ave, Cincinnati, OH 45230',0,'N/A',1,1,NULL),(12,'Beechmont Square','8550 Beechmont Ave, Cincinnati, OH 45255',0,'N/A',1,1,NULL),(13,'US Bank Ohio Pike','1259 Ohio Pike, Amelia, OH 45102',0,'N/A',1,1,NULL),(14,'US Bank Lunken Ops','5065 Wooster Pike, Cincinnati, OH 45226',0,'N/A',1,1,NULL),(15,'Krogers Mt Orab','210 Sterling Run Blvd, Mt Orab, OH 45154',0,'N/A',1,1,NULL),(16,'UC Aircare 3 Mt Orab','225 W Apple St, Mt Orab, OH 45154',0,'N/A',1,1,NULL),(17,'Milacron Mt Orab','418 W Main St, Mt Orab, OH 45154',0,'N/A',1,1,NULL),(18,'902 Fuel','4530 Eastgate Blvd Ste 500, Cincinnati, OH 45245',0,'N/A',1,1,NULL);
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `signup_requests`
--

DROP TABLE IF EXISTS `signup_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `signup_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `role` enum('Admin','Manager','Subcontractor') DEFAULT 'Subcontractor',
  `request_date` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `signup_requests`
--

LOCK TABLES `signup_requests` WRITE;
/*!40000 ALTER TABLE `signup_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `signup_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subcontractors`
--

DROP TABLE IF EXISTS `subcontractors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subcontractors` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subcontractors`
--

LOCK TABLES `subcontractors` WRITE;
/*!40000 ALTER TABLE `subcontractors` DISABLE KEYS */;
/*!40000 ALTER TABLE `subcontractors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `timesheets`
--

DROP TABLE IF EXISTS `timesheets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `timesheets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subcontractor_name` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  `hours` decimal(5,2) NOT NULL,
  `work_date` date NOT NULL,
  `notes` text,
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `timesheets`
--

LOCK TABLES `timesheets` WRITE;
/*!40000 ALTER TABLE `timesheets` DISABLE KEYS */;
/*!40000 ALTER TABLE `timesheets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `role` enum('Admin','Manager','Subcontractor') DEFAULT 'Subcontractor',
  `password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=62 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (50,'tony newport','555-555-5555','tnewport@communitygreengroup.com','Admin','$2b$12$saz8gMELUuvkXn7i5wRChOlFa9WC2001g/9rKhFIv.I1DCEeyVeV.'),(51,'Johnny Walker','555-555-5555','johnnywalker@communitygreengroup.com','Manager','$2b$12$ZoHSEmdVnKbcjxGq6kw1duyonOvFHzHX90jPBgPJ0NOoSGpwzti1m'),(52,'Buffalo Trace','555-555-5555','buffalotrace@communitygreengroup.com','Subcontractor','$2b$12$aMhAWzAomozcgSIwus64/.8ACrdkRt6UY6TcOvRtXS6GykKAfYilq'),(53,'Jesse Talmadge','555-555-5555','onebadmk8@gmail.com','Admin','$2b$12$cQEYjtzWhztdmFoX23Er2uX0o0Mtyqu4rKPnlMW3UOehI4pC0ue.G'),(54,'Eagle Rare','555-555-5555','eaglerare@bourbon.com','Manager','$2b$12$tZ/pHL97Yfxy0xmMkw39WO6HZeRGsVrgO1/ioqjRnLFrAIUchMmi2'),(55,'Pappy Van Winkle','555-555-5555','pappyvanwinkle@bourbon.com','Subcontractor','$2b$12$aoONE1JeeUmlK/qf6ndKDOBTDnK1Xq55oX2RDT9TCjMLXk/XWDMxq'),(56,'Christian Powers','555-555-5555','PowersPrecisionLLC@gmail.com','Admin','$2b$12$NJ0O.KcXUsNCA5y0rBF8dO1kzG/Ie8btiCnq4E7/Rst5gVYMsz2/S'),(57,'Blantons Whiskey','555-555-5555','blantonswhiskey@bourbon.com','Manager','$2b$12$pdDQrzUHFQY3UZbU5uqEuuV0SMRzFT5S8rzWe6qKXLil8i3i.uxP6'),(58,'EH Taylor','555-555-5555','ehtaylor@bourbon.com','Subcontractor','$2b$12$wpLWgf/hqiwvyl4M.KrpH.09mIsQ6aG9cMDSTgjU7lJ2IZwSRWwZy'),(59,'Josh Grace','555-555-5555','contractorappdev@gmail.com','Admin','$2b$12$BK5q02uynrUgCDBeW7J77Ov13v61jm9z5X0whYwRCxeUAyPLGN.h.'),(60,'Willett Pot','555-555-5555','willettpot@bourbon.com','Manager','$2b$12$iEKlpN8/vTrkpAY0pgTEBOKIILkjQLBvK3Z8ldcEQFvERZYHkjG3W'),(61,'Wild Turkey','555-555-5555','wildturkey@bourbon.com','Subcontractor','$2b$12$GT31Iej8wiPX7rgOXdPgb.AqIVrllcNmGqxcTGC/hDt.T76l.JXQu');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `winter_ops_logs`
--

DROP TABLE IF EXISTS `winter_ops_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `winter_ops_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `property_id` int DEFAULT NULL,
  `subcontractor_name` varchar(255) DEFAULT NULL,
  `time_in` datetime DEFAULT NULL,
  `time_out` datetime DEFAULT NULL,
  `bulk_salt_qty` decimal(10,2) DEFAULT NULL,
  `bag_salt_qty` decimal(10,2) DEFAULT NULL,
  `calcium_chloride_qty` decimal(10,2) DEFAULT NULL,
  `customer_provided` tinyint(1) DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  CONSTRAINT `winter_ops_logs_ibfk_1` FOREIGN KEY (`property_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `winter_ops_logs`
--

LOCK TABLES `winter_ops_logs` WRITE;
/*!40000 ALTER TABLE `winter_ops_logs` DISABLE KEYS */;
INSERT INTO `winter_ops_logs` VALUES (1,15,'bubbles','2025-03-11 19:30:00','2025-03-13 21:30:00',1.00,0.00,0.00,0,''),(2,8,'undefined','2025-02-02 05:45:00','2025-02-02 07:45:00',1.00,0.00,0.00,0,'BULK SALT WAS ACTIVATING WHEN I LEFT'),(3,14,'undefined','2025-02-12 18:30:00','2025-02-12 20:45:00',2.00,0.00,0.00,0,''),(4,5,'undefined','2025-02-10 05:45:00','2025-02-10 07:00:00',1.00,5.00,0.00,0,''),(5,10,'undefined','2025-02-11 02:30:00','2025-02-11 06:00:00',3.00,2.00,0.00,0,''),(6,12,'undefined','2025-04-01 15:00:00','2025-04-01 15:45:00',0.00,0.00,0.00,0,''),(7,7,'undefined','2025-02-05 09:00:00','2025-04-05 09:45:00',0.13,1.00,0.00,0,'');
/*!40000 ALTER TABLE `winter_ops_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `winter_products`
--

DROP TABLE IF EXISTS `winter_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `winter_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `winter_products`
--

LOCK TABLES `winter_products` WRITE;
/*!40000 ALTER TABLE `winter_products` DISABLE KEYS */;
INSERT INTO `winter_products` VALUES (1,'',''),(2,'Bulk Salt','yards'),(3,'Rock Salt','bags'),(4,'Calcium chloride','bags');
/*!40000 ALTER TABLE `winter_products` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-07 12:00:39
