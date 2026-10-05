-- Ajuste comprobado contra el catálogo remoto; no elimina registros.
-- El script de usuario de prueba lo ejecuta solo si existe la columna anterior.
ALTER TABLE public.equipos RENAME COLUMN problema_reportado TO falla_reportada;
