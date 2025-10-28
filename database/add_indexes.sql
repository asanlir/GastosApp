-- Script para añadir índices optimizados a una base de datos existente
-- Ejecutar este script si ya tienes las tablas creadas sin los índices nuevos

USE economia_db;

-- Índices adicionales para la tabla gastos
-- idx_anio_mes: optimiza ordenación DESC por año/mes y filtros por año
CREATE INDEX idx_anio_mes ON gastos (anio, mes);

-- idx_anio: optimiza agregaciones anuales (gráficos por año)
CREATE INDEX idx_anio ON gastos (anio);

-- idx_categoria_anio_mes: optimiza filtros combinados frecuentes (ej: gráficos de categoría específica por año)
CREATE INDEX idx_categoria_anio_mes ON gastos (categoria, anio, mes);

-- Índices adicionales para la tabla presupuesto
-- idx_anio_mes: optimiza búsquedas de presupuesto vigente con ordenación DESC
CREATE INDEX idx_anio_mes ON presupuesto (anio, mes);

-- Verificar índices creados
SHOW INDEX FROM gastos;
SHOW INDEX FROM presupuesto;
