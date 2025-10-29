-- Script para añadir ON UPDATE CASCADE a la foreign key de gastos
USE economia_db;

-- Primero, eliminar la constraint existente
ALTER TABLE gastos
DROP FOREIGN KEY gastos_ibfk_1;

-- Recrear la constraint con ON UPDATE CASCADE
ALTER TABLE gastos
ADD CONSTRAINT gastos_ibfk_1
FOREIGN KEY (categoria) REFERENCES categorias(nombre)
ON UPDATE CASCADE
ON DELETE RESTRICT;
