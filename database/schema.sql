-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS economia_db;
USE economia_db;

-- Tabla de categorías
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla de presupuesto
CREATE TABLE IF NOT EXISTS presupuesto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    monto DECIMAL(10,2) NOT NULL,
    fecha_cambio DATETIME NOT NULL,
    mes VARCHAR(20) NOT NULL,
    anio INT NOT NULL,
    INDEX idx_mes_anio (mes, anio)
);

-- Tabla de gastos
CREATE TABLE IF NOT EXISTS gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria VARCHAR(100) NOT NULL,
    descripcion TEXT,
    monto DECIMAL(10,2) NOT NULL,
    mes VARCHAR(20) NOT NULL,
    anio INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_categoria (categoria),
    INDEX idx_mes_anio (mes, anio),
    FOREIGN KEY (categoria) REFERENCES categorias(nombre)
);