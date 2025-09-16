-- Agregar campo para URLs de imágenes a productos
-- Julia Confecciones - Integración de imágenes genéricas

-- 1. Agregar campo para URL de imagen principal
ALTER TABLE productos ADD COLUMN IF NOT EXISTS imagen_url TEXT;

-- 2. Agregar campo para múltiples imágenes (opcional)
ALTER TABLE productos ADD COLUMN IF NOT EXISTS imagenes JSONB;

-- 3. Verificar que los campos se agregaron correctamente
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'productos'
AND column_name IN ('imagen_url', 'imagenes')
ORDER BY ordinal_position;

-- 4. Mostrar estructura completa de productos
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'productos'
ORDER BY ordinal_position;

-- 5. Contar productos antes de la actualización
SELECT COUNT(*) as total_productos FROM productos;