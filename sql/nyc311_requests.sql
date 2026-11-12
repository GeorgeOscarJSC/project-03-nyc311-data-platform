--
-- PostgreSQL database dump
--

\restrict EEIAeMIWMjr4mctGv41vZJan2QrVUjf2tBUK3BEx2SFe0i1njJxKdDHzihjuJfw

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: nyc311_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nyc311_requests (
    unique_key text NOT NULL,
    created_date timestamp without time zone,
    closed_date timestamp without time zone,
    agency text,
    complaint_type text,
    status text,
    borough text,
    raw_data jsonb NOT NULL,
    ingested_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: nyc311_requests nyc311_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nyc311_requests
    ADD CONSTRAINT nyc311_requests_pkey PRIMARY KEY (unique_key);


--
-- PostgreSQL database dump complete
--

\unrestrict EEIAeMIWMjr4mctGv41vZJan2QrVUjf2tBUK3BEx2SFe0i1njJxKdDHzihjuJfw

