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
    'pending',
    'processing',
    'shipped',
    'delivered',
    'cancelled',
    'failed',
    'return_requested',
    'returned',
    'refunded'
);


--
-- Name: log_order_status_change(); Type: FUNCTION; Schema: orders; Owner: -
--

CREATE FUNCTION orders.log_order_status_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    DECLARE
        changed_by_user INTEGER;
    BEGIN
        changed_by_user := NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER;
        
        IF NEW.status IS DISTINCT FROM OLD.status THEN
            INSERT INTO orders.order_status_history (
                order_id,
                old_status,
                new_status,
                changed_at,
                changed_by,
                note
            )
            VALUES (
                NEW.order_id,
                OLD.status,
                NEW.status,
                NOW(),
                changed_by_user,
                NULL
            );
        END IF;
        RETURN NEW;
    END;
    $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cart_items; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.cart_items (
    cart_id integer NOT NULL,
    product_id integer NOT NULL,
    add_to_cart_order integer NOT NULL,
    reordered integer NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT ck_cartitem_add_to_cart_order_nonnegative CHECK ((add_to_cart_order >= 0)),
    CONSTRAINT ck_cartitem_quantity_positive CHECK ((quantity > 0)),
    CONSTRAINT ck_cartitem_reordered_bool CHECK ((reordered = ANY (ARRAY[0, 1])))
);


--
-- Name: carts; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.carts (
    cart_id integer NOT NULL,
    user_id integer NOT NULL,
    total_items integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_cart_total_items_nonnegative CHECK ((total_items >= 0))
);


--
-- Name: carts_cart_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.carts_cart_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: carts_cart_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.carts_cart_id_seq OWNED BY orders.carts.cart_id;


--
-- Name: order_items; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.order_items (
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    add_to_cart_order integer NOT NULL,
    reordered integer NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT ck_orderitem_add_to_cart_order_nonnegative CHECK ((add_to_cart_order >= 0)),
    CONSTRAINT ck_orderitem_quantity_positive CHECK ((quantity > 0)),
    CONSTRAINT ck_orderitem_reordered_bool CHECK ((reordered = ANY (ARRAY[0, 1])))
);


--
-- Name: order_status_history; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.order_status_history (
    history_id integer NOT NULL,
    order_id integer NOT NULL,
    old_status public.order_status_enum,
    new_status public.order_status_enum NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    changed_by integer,
    note text
);


--
-- Name: order_status_history_history_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.order_status_history_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_status_history_history_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.order_status_history_history_id_seq OWNED BY orders.order_status_history.history_id;


--
-- Name: orders; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.orders (
    order_id integer NOT NULL,
    user_id integer NOT NULL,
    order_number integer NOT NULL,
    order_dow integer NOT NULL,
    order_hour_of_day integer NOT NULL,
    days_since_prior_order integer,
    total_items integer NOT NULL,
    status public.order_status_enum NOT NULL,
    delivery_name character varying(100),
    phone_number character varying(50),
    street_address character varying(255),
    city character varying(100),
    postal_code character varying(20),
    country character varying(100),
    tracking_number character varying(100),
    shipping_carrier character varying(50),
    tracking_url character varying(255),
    invoice bytea,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT ck_order_total_items_nonnegative CHECK ((total_items >= 0))
);


--
-- Name: orders_order_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.orders_order_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_order_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.orders_order_id_seq OWNED BY orders.orders.order_id;


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
-- Name: product_enriched; Type: TABLE; Schema: products; Owner: -
--

CREATE TABLE products.product_enriched (
    product_id integer NOT NULL,
    description text,
    price numeric(10,2),
    image_url text
);


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
    user_id integer NOT NULL,
    first_name character varying NOT NULL,
    last_name character varying NOT NULL,
    hashed_password character varying(128) NOT NULL,
    email_address character varying NOT NULL,
    phone_number character varying(50),
    street_address character varying(255),
    city character varying(100),
    postal_code character varying(20),
    country character varying(100),
    last_login timestamp with time zone,
    last_notifications_viewed_at timestamp with time zone,
    days_between_order_notifications integer,
    order_notifications_start_date_time timestamp with time zone,
    order_notifications_next_scheduled_time timestamp with time zone,
    last_notification_sent_at timestamp with time zone,
    pending_order_notification boolean NOT NULL,
    order_notifications_via_email boolean NOT NULL,
    CONSTRAINT check_days_between_order_notifications CHECK (((days_between_order_notifications IS NULL) OR ((days_between_order_notifications >= 1) AND (days_between_order_notifications <= 365))))
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: users; Owner: -
--

CREATE SEQUENCE users.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: users; Owner: -
--

ALTER SEQUENCE users.users_user_id_seq OWNED BY users.users.user_id;


--
-- Name: carts cart_id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.carts ALTER COLUMN cart_id SET DEFAULT nextval('orders.carts_cart_id_seq'::regclass);


--
-- Name: order_status_history history_id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_status_history ALTER COLUMN history_id SET DEFAULT nextval('orders.order_status_history_history_id_seq'::regclass);


--
-- Name: orders order_id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders ALTER COLUMN order_id SET DEFAULT nextval('orders.orders_order_id_seq'::regclass);


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
-- Name: users user_id; Type: DEFAULT; Schema: users; Owner: -
--

ALTER TABLE ONLY users.users ALTER COLUMN user_id SET DEFAULT nextval('users.users_user_id_seq'::regclass);


--
-- Name: cart_items cart_items_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.cart_items
    ADD CONSTRAINT cart_items_pkey PRIMARY KEY (cart_id, product_id);


--
-- Name: carts carts_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.carts
    ADD CONSTRAINT carts_pkey PRIMARY KEY (cart_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_id, product_id);


--
-- Name: order_status_history order_status_history_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_status_history
    ADD CONSTRAINT order_status_history_pkey PRIMARY KEY (history_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: aisles aisles_aisle_key; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.aisles
    ADD CONSTRAINT aisles_aisle_key UNIQUE (aisle);


--
-- Name: aisles aisles_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.aisles
    ADD CONSTRAINT aisles_pkey PRIMARY KEY (aisle_id);


--
-- Name: departments departments_department_key; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.departments
    ADD CONSTRAINT departments_department_key UNIQUE (department);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);


--
-- Name: product_enriched product_enriched_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.product_enriched
    ADD CONSTRAINT product_enriched_pkey PRIMARY KEY (product_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: users; Owner: -
--

ALTER TABLE ONLY users.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_orders_cart_items_product_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_cart_items_product_id ON orders.cart_items USING btree (product_id);


--
-- Name: ix_orders_carts_user_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_carts_user_id ON orders.carts USING btree (user_id);


--
-- Name: ix_orders_order_items_product_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_order_items_product_id ON orders.order_items USING btree (product_id);


--
-- Name: ix_orders_order_status_history_changed_at; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_order_status_history_changed_at ON orders.order_status_history USING btree (changed_at);


--
-- Name: ix_orders_order_status_history_order_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_order_status_history_order_id ON orders.order_status_history USING btree (order_id);


--
-- Name: ix_orders_orders_user_id; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_orders_user_id ON orders.orders USING btree (user_id);


--
-- Name: ix_orders_userid_orderid; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orders_userid_orderid ON orders.orders USING btree (user_id, order_id);


--
-- Name: ix_orderstatushistory_orderid_changedat; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX ix_orderstatushistory_orderid_changedat ON orders.order_status_history USING btree (order_id, changed_at);


--
-- Name: ix_products_products_aisle_id; Type: INDEX; Schema: products; Owner: -
--

CREATE INDEX ix_products_products_aisle_id ON products.products USING btree (aisle_id);


--
-- Name: ix_products_products_department_id; Type: INDEX; Schema: products; Owner: -
--

CREATE INDEX ix_products_products_department_id ON products.products USING btree (department_id);


--
-- Name: ix_products_products_product_name; Type: INDEX; Schema: products; Owner: -
--

CREATE INDEX ix_products_products_product_name ON products.products USING btree (product_name);


--
-- Name: ix_users_users_email_address; Type: INDEX; Schema: users; Owner: -
--

CREATE UNIQUE INDEX ix_users_users_email_address ON users.users USING btree (email_address);


--
-- Name: orders trg_order_status_change; Type: TRIGGER; Schema: orders; Owner: -
--

CREATE TRIGGER trg_order_status_change AFTER UPDATE OF status ON orders.orders FOR EACH ROW EXECUTE FUNCTION orders.log_order_status_change();

ALTER TABLE orders.orders DISABLE TRIGGER trg_order_status_change;


--
-- Name: cart_items cart_items_cart_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.cart_items
    ADD CONSTRAINT cart_items_cart_id_fkey FOREIGN KEY (cart_id) REFERENCES orders.carts(cart_id);


--
-- Name: cart_items cart_items_product_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.cart_items
    ADD CONSTRAINT cart_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id);


--
-- Name: carts carts_user_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.carts
    ADD CONSTRAINT carts_user_id_fkey FOREIGN KEY (user_id) REFERENCES users.users(user_id);


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
-- Name: order_status_history order_status_history_order_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_status_history
    ADD CONSTRAINT order_status_history_order_id_fkey FOREIGN KEY (order_id) REFERENCES orders.orders(order_id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES users.users(user_id);


--
-- Name: product_enriched product_enriched_product_id_fkey; Type: FK CONSTRAINT; Schema: products; Owner: -
--

ALTER TABLE ONLY products.product_enriched
    ADD CONSTRAINT product_enriched_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id);


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

