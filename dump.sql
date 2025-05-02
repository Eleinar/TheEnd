PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Предприниматель', 'Технолог', 'Помощник', 'Администратор'))
);
INSERT INTO Users VALUES(1,'admin','$2b$12$6buo.wOkBfujJT4Srr.bj.jL38xzZ5onAZhK.vTJ4nm/vcomb9rX6','Администратор');
INSERT INTO Users VALUES(2,'makariev','$2b$12$FM1D1UjNyt3kISzkDw20g.0ZwRYlhlv/HSIl/wiW1JOlOO0Vtspki','Предприниматель');
CREATE TABLE raw_materials (
	material_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	quantity FLOAT NOT NULL, 
	cost FLOAT NOT NULL, 
	purchase_date VARCHAR(10) NOT NULL, 
	PRIMARY KEY (material_id)
);
INSERT INTO raw_materials VALUES(1,'Мед',90.0,300.0,'2025-01-15');
INSERT INTO raw_materials VALUES(2,'Вода',1000.0,10.0,'2025-01-20');
INSERT INTO raw_materials VALUES(3,'Дрожжи',50.0,200.0,'2025-02-01');
INSERT INTO raw_materials VALUES(4,'Сахар',200.0,50.0,'2025-02-10');
INSERT INTO raw_materials VALUES(5,'Ягоды',150.0,150.0,'2025-03-05');
INSERT INTO raw_materials VALUES(6,'Хмель',20.0,500.0,'2025-03-15');
INSERT INTO raw_materials VALUES(7,'Лимонная кислота',30.0,100.0,'2025-04-01');
CREATE TABLE recipes (
	recipe_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR NOT NULL, 
	PRIMARY KEY (recipe_id)
);
INSERT INTO recipes VALUES(1,'Медовуха классическая','Мед, вода, дрожжи, 14 дней брожения');
INSERT INTO recipes VALUES(2,'Медовуха ягодная','Мед, вода, ягоды, дрожжи, 16 дней брожения');
INSERT INTO recipes VALUES(3,'Медовый эль','Мед, вода, хмель, дрожжи, 20 дней брожения');
INSERT INTO recipes VALUES(4,'Медовуха сладкая','Мед, вода, сахар, дрожжи, 12 дней брожения');
INSERT INTO recipes VALUES(5,'Медовуха кислая','Мед, вода, лимонная кислота, дрожжи, 15 дней брожения');
CREATE TABLE clients (
	client_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	type VARCHAR(10) NOT NULL, 
	contact VARCHAR(100) NOT NULL, 
	inn VARCHAR(12), 
	PRIMARY KEY (client_id)
);
INSERT INTO clients VALUES(1,'ООО "Медовый край"','Юрлицо','info@medkray.ru','123456789012');
INSERT INTO clients VALUES(2,'ИП Иванов А.В.','ИП','+7-900-123-45-67','9876543210');
INSERT INTO clients VALUES(3,'Магазин "Здоровье"','Юрлицо','shop@zdorovie.ru','456789123456');
INSERT INTO clients VALUES(4,'Петров Сергей','Физлицо','+7-911-234-56-78',NULL);
INSERT INTO clients VALUES(5,'Кафе "Улей"','Юрлицо','cafe@uley.ru','789123456789');
INSERT INTO clients VALUES(6,'Сидоров Николай','Физлицо','+7-922-345-67-89',NULL);
INSERT INTO clients VALUES(7,'ООО "Напитки"','Юрлицо','sales@napitki.ru','321654987123');
CREATE TABLE batches (
	batch_id INTEGER NOT NULL, 
	recipe_id INTEGER NOT NULL, 
	volume FLOAT NOT NULL, 
	start_date VARCHAR(10) NOT NULL, 
	end_date VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	user_id INTEGER NOT NULL, price_per_liter REAL NOT NULL DEFAULT 500.0, 
	PRIMARY KEY (batch_id), 
	FOREIGN KEY(recipe_id) REFERENCES recipes (recipe_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);
INSERT INTO batches VALUES(1,1,200.0,'2025-02-01','2025-02-15','Готова',1,600.0);
INSERT INTO batches VALUES(2,2,150.0,'2025-02-05','2025-02-21','Готова',1,500.0);
INSERT INTO batches VALUES(3,3,100.0,'2025-02-10','2025-03-02','Готова',1,500.0);
INSERT INTO batches VALUES(4,4,250.0,'2025-03-01','2025-03-13','Готова',1,500.0);
INSERT INTO batches VALUES(5,5,180.0,'2025-03-10','2025-03-25','Готова',1,500.0);
INSERT INTO batches VALUES(6,1,300.0,'2025-04-01','2025-04-15','Готова',1,500.0);
INSERT INTO batches VALUES(7,2,120.0,'2025-04-05','2025-04-21','Готова',1,500.0);
INSERT INTO batches VALUES(8,1,250.0,'2025-04-09','2025-04-23','В брожении',2,500.0);
INSERT INTO batches VALUES(9,1,250.0,'2025-04-16','2025-04-30','Готова',2,500.0);
INSERT INTO batches VALUES(10,1,10.0,'2025-04-16','2025-04-30','Готова',2,300.0);
CREATE TABLE orders (
	order_id INTEGER NOT NULL, 
	client_id INTEGER NOT NULL, 
	order_date VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	user_id INTEGER NOT NULL, 
	total_order_cost FLOAT NOT NULL, 
	PRIMARY KEY (order_id), 
	FOREIGN KEY(client_id) REFERENCES clients (client_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id)
);
INSERT INTO orders VALUES(1,1,'2025-02-20','Выполнен',1,90000.0);
INSERT INTO orders VALUES(2,2,'2025-02-25','Выполнен',1,32500.0);
INSERT INTO orders VALUES(3,3,'2025-03-05','Завершен',1,56000.0);
INSERT INTO orders VALUES(4,4,'2025-03-15','Выполняется',1,12400.0);
INSERT INTO orders VALUES(5,5,'2025-03-20','Завершен',1,93000.0);
INSERT INTO orders VALUES(6,6,'2025-04-05','Выполнен',1,7200.0);
INSERT INTO orders VALUES(7,7,'2025-04-08','Завершен',1,78000.0);
CREATE TABLE batch_materials (
	batch_id INTEGER NOT NULL, 
	material_id INTEGER NOT NULL, 
	used_quantity FLOAT NOT NULL, 
	PRIMARY KEY (batch_id, material_id), 
	FOREIGN KEY(batch_id) REFERENCES batches (batch_id), 
	FOREIGN KEY(material_id) REFERENCES raw_materials (material_id)
);
CREATE TABLE finished_products (
	product_id INTEGER NOT NULL, 
	batch_id INTEGER NOT NULL, 
	volume FLOAT NOT NULL, 
	available_volume FLOAT NOT NULL, 
	production_date VARCHAR(10) NOT NULL, 
	price_per_liter FLOAT NOT NULL, 
	PRIMARY KEY (product_id), 
	UNIQUE (batch_id), 
	FOREIGN KEY(batch_id) REFERENCES batches (batch_id)
);
INSERT INTO finished_products VALUES(1,9,250.0,250.0,'2025-04-30',500.0);
INSERT INTO finished_products VALUES(2,1,200.0,200.0,'2025-02-15',600.0);
INSERT INTO finished_products VALUES(3,2,150.0,150.0,'2025-02-21',500.0);
INSERT INTO finished_products VALUES(4,3,100.0,100.0,'2025-03-02',500.0);
INSERT INTO finished_products VALUES(5,4,250.0,250.0,'2025-03-13',500.0);
INSERT INTO finished_products VALUES(6,5,180.0,180.0,'2025-03-25',500.0);
INSERT INTO finished_products VALUES(7,6,300.0,300.0,'2025-04-15',500.0);
INSERT INTO finished_products VALUES(8,7,120.0,120.0,'2025-04-21',500.0);
INSERT INTO finished_products VALUES(9,10,10.0,10.0,'2025-04-30',300.0);
CREATE TABLE order_items (
	item_id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	volume FLOAT NOT NULL, 
	total_cost FLOAT NOT NULL, 
	PRIMARY KEY (item_id), 
	FOREIGN KEY(order_id) REFERENCES orders (order_id), 
	FOREIGN KEY(product_id) REFERENCES finished_products (product_id)
);
INSERT INTO order_items VALUES(1,1,1,150.0,90000.0);
INSERT INTO order_items VALUES(2,2,2,50.0,32500.0);
INSERT INTO order_items VALUES(3,3,3,80.0,56000.0);
INSERT INTO order_items VALUES(4,4,4,20.0,11000.0);
INSERT INTO order_items VALUES(5,4,5,2.0,1240.0);
INSERT INTO order_items VALUES(6,5,4,150.0,82500.0);
INSERT INTO order_items VALUES(7,5,1,15.0,9000.0);
INSERT INTO order_items VALUES(8,6,5,10.0,6200.0);
INSERT INTO order_items VALUES(9,6,2,1.0,650.0);
INSERT INTO order_items VALUES(10,7,6,120.0,72000.0);
INSERT INTO order_items VALUES(11,7,3,10.0,7000.0);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('Users',2);
COMMIT;
