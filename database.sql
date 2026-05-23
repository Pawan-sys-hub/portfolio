-- ============================================================
-- Portfolio Website Database Schema
-- Run against your existing 'pawan' database:
--   mysql -u root -p pawan < database.sql
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
INSERT INTO projects (title, category, description, image_url, live_link, git_link, technologies_used) VALUES
(
    'ShopNest E-Commerce',
    'Web App',
    'A full-featured online store with product catalogue, cart management, Stripe payment integration, and an admin dashboard for inventory control. Achieved sub-2-second page loads via Redis caching.',
    'https://images.unsplash.com/photo-1556742502-ec7c0e9f34b1?w=800&q=80',
    'https://shopnest.example.com',
    'https://github.com/yourname/shopnest',
    'React, Node.js, Express, MongoDB, Redis, Stripe API, TailwindCSS'
),
(
    'TaskFlow – Project Manager',
    'Web App',
    'A Kanban-style project management tool supporting real-time drag-and-drop columns, team member assignment, due-date reminders via email, and activity logs. Built with WebSockets for instant collaboration.',
    'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800&q=80',
    'https://taskflow.example.com',
    'https://github.com/yourname/taskflow',
    'Vue 3, Python, FastAPI, PostgreSQL, Socket.IO, Docker, AWS S3'
),
(
    'WeatherLens Mobile App',
    'Mobile',
    'A cross-platform weather application delivering hyper-local 7-day forecasts, animated weather conditions, push notifications for severe alerts, and an interactive radar map overlay.',
    'https://images.unsplash.com/photo-1504608524841-42584120d693?w=800&q=80',
    'https://weatherlens.example.com',
    'https://github.com/yourname/weatherlens',
    'React Native, Expo, OpenWeatherMap API, AsyncStorage, Lottie'
);
