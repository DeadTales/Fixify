-- ==========================================
-- 1. TABLAS PRINCIPALES (Sin llaves foráneas)
-- ==========================================

-- AG-138 / AG-140 / AG-141: Registro de clientes con restricción de unicidad para evitar duplicados
CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE materiales (
    id_material SERIAL PRIMARY KEY,
    descripcion VARCHAR(200) NOT NULL,
    existencia_actual INT DEFAULT 0 CHECK (existencia_actual >= 0),
    stock_minimo INT DEFAULT 0 CHECK (stock_minimo >= 0)
);

-- ==========================================
-- 2. TABLAS DE PRIMER NIVEL DE DEPENDENCIA
-- ==========================================

-- AG-134 / AG-135 / AG-136 / AG-137: Usuarios con campo de activación/desactivación y roles
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INT NOT NULL REFERENCES roles(id_rol),
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL, -- Soporte para activar/desactivar usuario
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AG-143 / AG-145 / AG-146: Registro de equipo, datos obligatorios y relación con cliente
CREATE TABLE equipos (
    id_equipo SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    tipo VARCHAR(50) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    numero_serie VARCHAR(100),
    falla_reportada TEXT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. TABLA CENTRAL Y LÓGICA DE FOLIOS (AG-144)
-- ==========================================

CREATE TABLE ordenes_servicio (
    id_orden SERIAL PRIMARY KEY,
    folio VARCHAR(50) UNIQUE NOT NULL,
    id_equipo INT NOT NULL REFERENCES equipos(id_equipo),
    id_cliente INT NOT NULL REFERENCES clientes(id_cliente),
    id_tecnico INT REFERENCES usuarios(id_usuario),
    estado VARCHAR(50) NOT NULL DEFAULT 'Recibido',
    fecha_recepcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP NULL
);

-- Función y Trigger para autogenerar folio único (AG-144)
CREATE OR REPLACE FUNCTION generar_folio_orden()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.folio IS NULL OR NEW.folio = '' THEN
        NEW.folio := 'FIX-' || LPAD(NEXTVAL('ordenes_servicio_id_orden_seq')::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generar_folio
BEFORE INSERT ON ordenes_servicio
FOR EACH ROW
EXECUTE FUNCTION generar_folio_orden();

-- ==========================================
-- 4. TABLAS DE SEGUNDO NIVEL (Historial y Detalles)
-- ==========================================

CREATE TABLE diagnosticos (
    id_diagnostico SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes_servicio(id_orden) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE actividades_reparacion (
    id_actividad SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes_servicio(id_orden) ON DELETE CASCADE,
    trabajo_realizado TEXT NOT NULL,
    solucion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consumos_material (
    id_consumo SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes_servicio(id_orden) ON DELETE CASCADE,
    id_material INT NOT NULL REFERENCES materiales(id_material),
    cantidad_utilizada INT NOT NULL CHECK (cantidad_utilizada > 0)
);

CREATE TABLE historial_estados (
    id_historial SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes_servicio(id_orden) ON DELETE CASCADE,
    id_usuario INT NOT NULL REFERENCES usuarios(id_usuario),
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50) NOT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 5. DATOS DE PRUEBA ACTUALIZADOS
-- ==========================================

INSERT INTO roles (nombre_rol) VALUES 
('Administrador'), 
('Técnico'), 
('Recepcionista');

INSERT INTO clientes (nombre, telefono, correo) VALUES 
('Juan Pérez', '3312345678', 'juan.perez@correo.com'),
('María Gómez', '3387654321', 'maria.gomez@correo.com');

INSERT INTO materiales (descripcion, existencia_actual, stock_minimo) VALUES 
('Pantalla de repuesto', 5, 2), 
('Pasta térmica', 15, 3),
('Batería genérica', 8, 2);

-- Inserción de usuarios incluyendo el campo "activo"
INSERT INTO usuarios (id_rol, nombre, correo, contrasena_hash, activo) VALUES 
(1, 'Carlos Admin', 'admin@fixify.com', 'hash_falso_admin', TRUE),
(2, 'Roberto Técnico', 'tecnico@fixify.com', 'hash_falso_tecnico', TRUE);

INSERT INTO equipos (id_cliente, tipo, marca, modelo, numero_serie, falla_reportada) VALUES 
(1, 'Smartphone', 'Xiaomi', '14T', 'SN-X14T-001', 'Módulo de cámaras rayado y no enfoca bien'),
(2, 'Computadora de Escritorio', 'Custom', 'Intel Core i5-9400F', 'SN-PC-998', 'Apagados repentinos por altas temperaturas');

-- El folio se genera automáticamente mediante el trigger si no se especifica explícitamente
INSERT INTO ordenes_servicio (id_equipo, id_cliente, id_tecnico, estado, folio) VALUES 
(1, 1, 2, 'Recibido', 'FIX-000001'),
(2, 2, 2, 'En Diagnóstico', 'FIX-000002');

INSERT INTO diagnosticos (id_orden, descripcion) VALUES 
(2, 'Se detectó que el disipador del procesador está obstruido y requiere limpieza profunda.');