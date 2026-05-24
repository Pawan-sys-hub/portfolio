-- ============================================================
-- Portfolio Website Database Schema
-- Run against your existing 'pawan' database:
--   mysql -u pawan -p pawan < database.sql
-- ============================================================

USE pawan;

-- ============================================================
-- Table: projects
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id                INT UNSIGNED     NOT NULL AUTO_INCREMENT,
    title             VARCHAR(120)     NOT NULL,
    category          VARCHAR(60)      NOT NULL,
    description       TEXT             NOT NULL,
    image_url         VARCHAR(255)     NOT NULL DEFAULT '',
    live_link         VARCHAR(255)     NOT NULL DEFAULT '',
    git_link          VARCHAR(255)     NOT NULL DEFAULT '',
    technologies_used VARCHAR(255)     NOT NULL DEFAULT '',
    created_at        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: contact_messages
-- ============================================================
CREATE TABLE IF NOT EXISTS contact_messages (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(120) NOT NULL,
    email      VARCHAR(180) NOT NULL,
    subject    VARCHAR(200) NOT NULL,
    message    TEXT         NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Seed Data: 3 realistic sample projects
-- ============================================================

INSERT INTO projects (title, category, description, image_url, live_link, git_link, technologies_used)
VALUES
('Portfolio Website', 'Web App', 'My personal portfolio', '', '', '', 'Flask,MySQL,HTML,CSS');