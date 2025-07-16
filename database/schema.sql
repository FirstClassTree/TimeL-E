--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: orders; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA orders;


--
-- Name: products; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA products;


--
-- Name: users; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA users;


--
-- Name: order_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.order_status_enum AS ENUM (
    'PENDING',
    'PROCESSING',
    'SHIPPED',
    'DELIVERED',
    'CANCELLED',
    'FAILED',
    'RETURN_REQUESTED',
    'RETURNED',
    'REFUNDED'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: order_items; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.order_items (
    order_id uuid NOT NULL,
    product_id integer NOT NULL,
    add_to_cart_order integer NOT NULL,
    reordered integer NOT NULL,
    quantity integer NOT NULL
);


--
-- Name: orders; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.orders (
    order_id uuid NOT NULL,
    user_id uuid NOT NULL,
    eval_set character varying NOT NULL,
    order_number integer NOT NULL,
    order_dow integer NOT NULL,
    order_hour_of_day integer NOT NULL,
    days_since_prior_order double precision,
    total_items integer NOT NULL,
    status public.order_status_enum NOT NULL,
    phone_number character varying(20),
    street_address character varying(255),
    city character varying(100),
    postal_code character varying(20),
    country character varying(100),
    tracking_number character varying(100),
    shipping_carrier character varying(50),
    tracking_url character varying(255),
    invoice bytea
);


--
-- Name: aisles; Type: TABLE; Schema: products; Owner: -
--

CREATE TABLE products.aisles (
    aisle_id integer NOT NULL,
    aisle character varying(100) NOT NULL
);


--
-- Name: aisles_aisle_id_seq; Type: SEQUENCE; Schema: products; Owner: -
--

CREATE SEQUENCE products.aisles_aisle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: aisles_aisle_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: -
--

ALTER SEQUENCE products.aisles_aisle_id_seq OWNED BY products.aisles.aisle_id;


--
-- Name: departments; Type: TABLE; Schema: products; Owner: -
--

CREATE TABLE products.departments (
    department_id integer NOT NULL,
    department character varying(100) NOT NULL
);


--
-- Name: departments_department_id_seq; Type: SEQUENCE; Schema: products; Owner: -
--

CREATE SEQUENCE products.departments_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: departments_department_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: -
--

ALTER SEQUENCE products.departments_department_id_seq OWNED BY products.departments.department_id;


--
-- Name: products; Type: TABLE; Schema: products; Owner: -
--

CREATE TABLE products.products (
    product_id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    aisle_id integer NOT NULL,
    department_id integer NOT NULL
);


--
-- Name: products_product_id_seq; Type: SEQUENCE; Schema: products; Owner: -
--

CREATE SEQUENCE products.products_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: -
--

ALTER SEQUENCE products.products_product_id_seq OWNED BY products.products.product_id;


--
-- Name: users; Type: TABLE; Schema: users; Owner: -
--

CREATE TABLE users.users (
    user_id uuid NOT NULL,
    name character varying NOT NULL,
    hashed_password character varying(128) NOT NULL,
    email_address character varying NOT NULL,
    phone_number character varying(20) NOT NULL,
    street_address character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    postal_code character varying(20) NOT NULL,
    country character varying(100) NOT NULL
);


--
-- Name: aisles aisle_id; Type: DEFAULT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.aisles ALTER COLUMN aisle_id SET DEFAULT nextval('products.aisles_aisle_id_seq'::regclass);


--
-- Name: departments department_id; Type: DEFAULT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.departments ALTER COLUMN department_id SET DEFAULT nextval('products.departments_department_id_seq'::regclass);


--
-- Name: products product_id; Type: DEFAULT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.products ALTER COLUMN product_id SET DEFAULT nextval('products.products_product_id_seq'::regclass);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_id, product_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: aisles aisles_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.aisles
    ADD CONSTRAINT aisles_pkey PRIMARY KEY (aisle_id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: users users_name_key; Type: CONSTRAINT; Schema: users; Owner: -
--

ALTER TABLE ONLY users.users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: users; Owner: -
--

ALTER TABLE ONLY users.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_orders_order_items_product_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_order_items_product_id ON orders.order_items USING btree (product_id);


--
-- Name: ix_orders_orders_user_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_orders_user_id ON orders.orders USING btree (user_id);


--
-- Name: ix_products_products_aisle_id; Type: INDEX; Schema: products; Owner: -
--

CREATE INDEX ix_products_products_aisle_id ON products.products USING btree (aisle_id);


--
-- Name: ix_products_products_department_id; Type: INDEX; Schema: products; Owner: -
--

CREATE INDEX ix_products_products_department_id ON products.products USING btree (department_id);


--
-- Name: ix_users_users_email_address; Type: INDEX; Schema: users; Owner: -
--

CREATE UNIQUE INDEX ix_users_users_email_address ON users.users USING btree (email_address);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders.orders(order_id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES users.users(user_id);


--
-- Name: products products_aisle_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_aisle_id_fkey FOREIGN KEY (aisle_id) REFERENCES products.aisles(aisle_id);


--
-- Name: products products_department_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_department_id_fkey FOREIGN KEY (department_id) REFERENCES products.departments(department_id);


--
-- PostgreSQL database dump complete
--

