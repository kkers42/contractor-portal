CREATE TABLE IF NOT EXISTS identities (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  provider ENUM('google','microsoft','apple') NOT NULL,
  subject VARCHAR(190) NOT NULL,
  email VARCHAR(254) NULL,
  email_verified TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_provider_subject (provider, subject),
  KEY idx_user_provider (user_id, provider),
  CONSTRAINT fk_identities_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

ALTER TABLE users
  MODIFY COLUMN password_hash VARCHAR(255) NULL,
  MODIFY COLUMN password_salt VARCHAR(255) NULL,
  ADD COLUMN display_name VARCHAR(120) NULL AFTER email,
  ADD COLUMN avatar_url   VARCHAR(500) NULL AFTER display_name,
  ADD COLUMN last_login_at TIMESTAMP NULL AFTER updated_at;

ALTER TABLE users
  ADD UNIQUE KEY uq_users_email (email);
