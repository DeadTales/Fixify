-- ==========================================
-- CONSULTAS Y OPERACIONES PARA EL BACKEND (FIXIFY)
-- ==========================================

-- ------------------------------------------
-- 1. INICIO DE SESIÓN (LOGIN)[cite: 16]
-- ------------------------------------------
-- Verifica credenciales únicamente si el usuario está activo[cite: 17]
SELECT id_usuario, nombre, id_rol, contrasena_hash 
FROM usuarios 
WHERE correo = $1 AND activo = TRUE; --[cite: 17]


-- ------------------------------------------
-- 2. GESTIÓN DE USUARIOS (AG-134, AG-135, AG-136)[cite: 16]
-- ------------------------------------------
-- Crear usuario nuevo[cite: 16]
INSERT INTO usuarios (id_rol, nombre, correo, contrasena_hash) 
VALUES ($1, $2, $3, $4) 
RETURNING id_usuario, nombre, correo, id_rol, activo;

-- Desactivar usuario (AG-136)[cite: 17]
UPDATE usuarios 
SET activo = FALSE 
WHERE id_usuario = $1; --[cite: 17]

-- Activar usuario (AG-135)[cite: 17]
UPDATE usuarios 
SET activo = TRUE 
WHERE id_usuario = $1; --[cite: 17]


-- ------------------------------------------
-- 3. GESTIÓN DE CLIENTES (AG-138, AG-140, AG-146)[cite: 16]
-- ------------------------------------------
-- Crear cliente nuevo[cite: 16]
INSERT INTO clientes (nombre, telefono, correo) 
VALUES ($1, $2, $3) 
RETURNING id_cliente, nombre, telefono, correo;

-- Buscar cliente por correo o teléfono (Validación de existencia / Autocompletado)[cite: 17]
SELECT id_cliente, nombre, telefono, correo 
FROM clientes 
WHERE correo = $1 OR telefono = $2; --[cite: 17]


-- ------------------------------------------
-- 4. GESTIÓN DE EQUIPOS Y ÓRDENES (AG-143, AG-144, AG-145)[cite: 16]
-- ------------------------------------------
-- Registrar equipo asociado a un cliente existente[cite: 16, 18]
INSERT INTO equipos (id_cliente, tipo, marca, modelo, numero_serie, falla_reportada) 
VALUES ($1, $2, $3, $4, $5, $6) 
RETURNING id_equipo, id_cliente, tipo, marca, modelo, numero_serie;

-- Generar Orden de Servicio (El Trigger genera el folio automático FIX-00000X)[cite: 18]
INSERT INTO ordenes_servicio (id_equipo, id_cliente, id_tecnico, estado) 
VALUES ($1, $2, $3, 'Recibido') 
RETURNING id_orden, folio, fecha_recepcion;


/*
==========================================
DOCUMENTACIÓN DE CÓDIGOS DE ERROR (POSTGRESQL)[cite: 17]
==========================================
Compartir estos códigos con el desarrollador Backend para manejo de alertas (AG-142):[cite: 17]

- Error 23505 (unique_violation):[cite: 17]
  Ocurre al intentar registrar un correo duplicado en usuarios o clientes.[cite: 17]
  Mensaje a mostrar en pantalla: "El correo ingresado ya está registrado en el sistema."[cite: 17]

- Error 23503 (foreign_key_violation):[cite: 17]
  Ocurre si intentan registrar un equipo a un id_cliente que no existe.[cite: 17]
  Mensaje a mostrar en pantalla: "El cliente seleccionado no es válido o fue eliminado."[cite: 17]
*/