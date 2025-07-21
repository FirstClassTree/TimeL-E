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
-- Name: orders; Type: SCHEMA; Schema: -; Owner: timele_user
--

CREATE SCHEMA orders;


ALTER SCHEMA orders OWNER TO timele_user;

--
-- Name: products; Type: SCHEMA; Schema: -; Owner: timele_user
--

CREATE SCHEMA products;


ALTER SCHEMA products OWNER TO timele_user;

--
-- Name: users; Type: SCHEMA; Schema: -; Owner: timele_user
--

CREATE SCHEMA users;


ALTER SCHEMA users OWNER TO timele_user;

--
-- Name: order_status_enum; Type: TYPE; Schema: public; Owner: timele_user
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


ALTER TYPE public.order_status_enum OWNER TO timele_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: order_items; Type: TABLE; Schema: orders; Owner: timele_user
--

CREATE TABLE orders.order_items (
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    add_to_cart_order integer NOT NULL,
    reordered integer NOT NULL,
    quantity integer NOT NULL
);


ALTER TABLE orders.order_items OWNER TO timele_user;

--
-- Name: orders; Type: TABLE; Schema: orders; Owner: timele_user
--

CREATE TABLE orders.orders (
    order_id integer NOT NULL,
    user_id integer NOT NULL,
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


ALTER TABLE orders.orders OWNER TO timele_user;

--
-- Name: orders_order_id_seq; Type: SEQUENCE; Schema: orders; Owner: timele_user
--

CREATE SEQUENCE orders.orders_order_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE orders.orders_order_id_seq OWNER TO timele_user;

--
-- Name: orders_order_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: timele_user
--

ALTER SEQUENCE orders.orders_order_id_seq OWNED BY orders.orders.order_id;


--
-- Name: aisles; Type: TABLE; Schema: products; Owner: timele_user
--

CREATE TABLE products.aisles (
    aisle_id integer NOT NULL,
    aisle character varying(100) NOT NULL
);


ALTER TABLE products.aisles OWNER TO timele_user;

--
-- Name: aisles_aisle_id_seq; Type: SEQUENCE; Schema: products; Owner: timele_user
--

CREATE SEQUENCE products.aisles_aisle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE products.aisles_aisle_id_seq OWNER TO timele_user;

--
-- Name: aisles_aisle_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: timele_user
--

ALTER SEQUENCE products.aisles_aisle_id_seq OWNED BY products.aisles.aisle_id;


--
-- Name: departments; Type: TABLE; Schema: products; Owner: timele_user
--

CREATE TABLE products.departments (
    department_id integer NOT NULL,
    department character varying(100) NOT NULL
);


ALTER TABLE products.departments OWNER TO timele_user;

--
-- Name: departments_department_id_seq; Type: SEQUENCE; Schema: products; Owner: timele_user
--

CREATE SEQUENCE products.departments_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE products.departments_department_id_seq OWNER TO timele_user;

--
-- Name: departments_department_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: timele_user
--

ALTER SEQUENCE products.departments_department_id_seq OWNED BY products.departments.department_id;


--
-- Name: product_enriched; Type: TABLE; Schema: products; Owner: timele_user
--

CREATE TABLE products.product_enriched (
    product_id integer NOT NULL,
    description text,
    price numeric(10,2),
    image_url text
);


ALTER TABLE products.product_enriched OWNER TO timele_user;

--
-- Name: products; Type: TABLE; Schema: products; Owner: timele_user
--

CREATE TABLE products.products (
    product_id integer NOT NULL,
    product_name character varying(255) NOT NULL,
    aisle_id integer NOT NULL,
    department_id integer NOT NULL
);


ALTER TABLE products.products OWNER TO timele_user;

--
-- Name: products_product_id_seq; Type: SEQUENCE; Schema: products; Owner: timele_user
--

CREATE SEQUENCE products.products_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE products.products_product_id_seq OWNER TO timele_user;

--
-- Name: products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: products; Owner: timele_user
--

ALTER SEQUENCE products.products_product_id_seq OWNED BY products.products.product_id;


--
-- Name: users; Type: TABLE; Schema: users; Owner: timele_user
--

CREATE TABLE users.users (
    user_id integer NOT NULL,
    name character varying NOT NULL,
    hashed_password character varying(128) NOT NULL,
    email_address character varying NOT NULL,
    phone_number character varying(50) NOT NULL,
    street_address character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    postal_code character varying(20) NOT NULL,
    country character varying(100) NOT NULL
);


ALTER TABLE users.users OWNER TO timele_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: users; Owner: timele_user
--

CREATE SEQUENCE users.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE users.users_user_id_seq OWNER TO timele_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: users; Owner: timele_user
--

ALTER SEQUENCE users.users_user_id_seq OWNED BY users.users.user_id;


--
-- Name: orders order_id; Type: DEFAULT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.orders ALTER COLUMN order_id SET DEFAULT nextval('orders.orders_order_id_seq'::regclass);


--
-- Name: aisles aisle_id; Type: DEFAULT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.aisles ALTER COLUMN aisle_id SET DEFAULT nextval('products.aisles_aisle_id_seq'::regclass);


--
-- Name: departments department_id; Type: DEFAULT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.departments ALTER COLUMN department_id SET DEFAULT nextval('products.departments_department_id_seq'::regclass);


--
-- Name: products product_id; Type: DEFAULT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.products ALTER COLUMN product_id SET DEFAULT nextval('products.products_product_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: users; Owner: timele_user
--

ALTER TABLE ONLY users.users ALTER COLUMN user_id SET DEFAULT nextval('users.users_user_id_seq'::regclass);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_id, product_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: aisles aisles_pkey; Type: CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.aisles
    ADD CONSTRAINT aisles_pkey PRIMARY KEY (aisle_id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);


--
-- Name: product_enriched product_enriched_pkey; Type: CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.product_enriched
    ADD CONSTRAINT product_enriched_pkey PRIMARY KEY (product_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: users users_name_key; Type: CONSTRAINT; Schema: users; Owner: timele_user
--

ALTER TABLE ONLY users.users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: users; Owner: timele_user
--

ALTER TABLE ONLY users.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_orders_order_items_product_id; Type: INDEX; Schema: orders; Owner: timele_user
--

CREATE INDEX ix_orders_order_items_product_id ON orders.order_items USING btree (product_id);


--
-- Name: ix_orders_orders_user_id; Type: INDEX; Schema: orders; Owner: timele_user
--

CREATE INDEX ix_orders_orders_user_id ON orders.orders USING btree (user_id);


--
-- Name: ix_products_products_aisle_id; Type: INDEX; Schema: products; Owner: timele_user
--

CREATE INDEX ix_products_products_aisle_id ON products.products USING btree (aisle_id);


--
-- Name: ix_products_products_department_id; Type: INDEX; Schema: products; Owner: timele_user
--

CREATE INDEX ix_products_products_department_id ON products.products USING btree (department_id);


--
-- Name: ix_users_users_email_address; Type: INDEX; Schema: users; Owner: timele_user
--

CREATE UNIQUE INDEX ix_users_users_email_address ON users.users USING btree (email_address);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders.orders(order_id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: timele_user
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES users.users(user_id);


--
-- Name: product_enriched product_enriched_product_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.product_enriched
    ADD CONSTRAINT product_enriched_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id);


--
-- Name: products products_aisle_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_aisle_id_fkey FOREIGN KEY (aisle_id) REFERENCES products.aisles(aisle_id);


--
-- Name: products products_department_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: timele_user
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_department_id_fkey FOREIGN KEY (department_id) REFERENCES products.departments(department_id);


--
-- PostgreSQL database dump complete
--

