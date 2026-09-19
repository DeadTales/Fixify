-- Recrear la base de datos limpia
DROP DATABASE IF EXISTS fixify;
CREATE DATABASE fixify;
USE fixify;

-- ==========================================
-- 1. TABLAS PRINCIPALES (Sin llaves foráneas)
-- ==========================================

CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100)
);

CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL
);

CREATE TABLE materiales (
    id_material INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(200) NOT NULL,
    existencia_actual INT DEFAULT 0,
    stock_minimo INT DEFAULT 0
);

-- ==========================================
-- 2. TABLAS DE PRIMER NIVEL DE DEPENDENCIA
-- ==========================================

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_rol INT,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

CREATE TABLE equipos (
    id_equipo INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    tipo VARCHAR(50),
    marca VARCHAR(50),
    modelo VARCHAR(50),
    numero_serie VARCHAR(100),
    falla_reportada TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

-- ==========================================
-- 3. TABLA CENTRAL (Transaccional)
-- ==========================================

CREATE TABLE ordenes_servicio (
    id_orden INT AUTO_INCREMENT PRIMARY KEY,
    folio VARCHAR(50) UNIQUE NOT NULL,
    id_equipo INT NOT NULL,
    id_cliente INT NOT NULL,
    id_tecnico INT,
    estado VARCHAR(50) NOT NULL,
    fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP NULL,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id_equipo),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_tecnico) REFERENCES usuarios(id_usuario)
);

-- ==========================================
-- 4. TABLAS DE SEGUNDO NIVEL (Historial y Detalles)
-- ==========================================

CREATE TABLE diagnosticos (
    id_diagnostico INT AUTO_INCREMENT PRIMARY KEY,
    id_orden INT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_orden) REFERENCES ordenes_servicio(id_orden)
);

CREATE TABLE actividades_reparacion (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    id_orden INT NOT NULL,
    trabajo_realizado TEXT NOT NULL,
    solucion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_orden) REFERENCES ordenes_servicio(id_orden)
);

CREATE TABLE consumos_material (
    id_consumo INT AUTO_INCREMENT PRIMARY KEY,
    id_orden INT NOT NULL,
    id_material INT NOT NULL,
    cantidad_utilizada INT NOT NULL,
    FOREIGN KEY (id_orden) REFERENCES ordenes_servicio(id_orden),
    FOREIGN KEY (id_material) REFERENCES materiales(id_material)
);

CREATE TABLE historial_estados (
    id_historial INT AUTO_INCREMENT PRIMARY KEY,
    id_orden INT NOT NULL,
    id_usuario INT NOT NULL,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50) NOT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_orden) REFERENCES ordenes_servicio(id_orden),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);


-- ==========================================
-- 5. DATOS DE PRUEBA (Dummy Data)
-- ==========================================

-- Insertar Roles
INSERT INTO roles (nombre_rol) VALUES 
('Administrador (prueba)'), 
('Técnico (prueba)'), 
('Recepcionista (prueba)');

-- Insertar Clientes
INSERT INTO clientes (nombre, telefono, correo) VALUES 
('Juan Pérez (prueba)', '3312345678', 'juan.prueba@correo.com'),
('María Gómez (prueba)', '3387654321', 'maria.prueba@correo.com');

-- Insertar Materiales
INSERT INTO materiales (descripcion, existencia_actual, stock_minimo) VALUES 
('Pantalla de repuesto (prueba)', 5, 2), 
('Pasta térmica (prueba)', 15, 3),
('Batería genérica (prueba)', 8, 2);

-- Insertar Usuarios (Se asigna el id_rol 2 que corresponde a Técnico)
INSERT INTO usuarios (id_rol, nombre, correo, contrasena_hash) VALUES 
(2, 'Roberto Técnico (prueba)', 'tecnico.prueba@fixify.com', 'hash_falso_12345');

-- Insertar Equipos de los clientes
INSERT INTO equipos (id_cliente, tipo, marca, modelo, numero_serie, falla_reportada) VALUES 
(1, 'Smartphone (prueba)', 'Xiaomi', '14T', 'SN-X14T-001', 'Módulo de cámaras rayado y no enfoca bien (prueba)'),
(2, 'Computadora de Escritorio (prueba)', 'Custom', 'Intel Core i5-9400F', 'SN-PC-998', 'Apagados repentinos por altas temperaturas (prueba)');

-- Insertar una Orden de Servicio (Asignando el equipo 1, del cliente 1, al técnico 1)
INSERT INTO ordenes_servicio (folio, id_equipo, id_cliente, id_tecnico, estado) VALUES 
('FIX-001 (prueba)', 1, 1, 1, 'Recibido (prueba)'),
('FIX-002 (prueba)', 2, 2, 1, 'En Diagnóstico (prueba)');

-- Insertar un Diagnóstico inicial
INSERT INTO diagnosticos (id_orden, descripcion) VALUES 
(2, 'Se detectó que el disipador del procesador está obstruido y requiere limpieza profunda (prueba)');