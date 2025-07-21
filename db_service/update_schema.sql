-- Update schema to add enriched products table
-- Run this if the database already exists and you need to add the new table

CREATE TABLE IF NOT EXISTS products.product_enriched (
    product_id integer NOT NULL,
    description text,
    price numeric(10,2),
    image_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT product_enriched_pkey PRIMARY KEY (product_id),
    CONSTRAINT product_enriched_product_id_fkey FOREIGN KEY (product_id) REFERENCES products.products(product_id)
);

-- Add helpful comment
COMMENT ON TABLE products.product_enriched IS 'Enriched product data with descriptions, prices, and images from external APIs';
