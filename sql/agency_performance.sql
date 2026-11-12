--
-- PostgreSQL database dump
--

\restrict eRlIkjnyy5SgO488U94FcEV65zbZXEIsG1bp2ax5K3Punw95H6cec8hgqOmyJV9

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

--
-- Name: agency_performance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.agency_performance AS
 SELECT agency,
    count(*) AS total_requests,
    count(*) FILTER (WHERE (status = 'Closed'::text)) AS closed_requests,
    round(((100.0 * (count(*) FILTER (WHERE (status = 'Closed'::text)))::numeric) / (NULLIF(count(*), 0))::numeric), 2) AS closed_rate_pct
   FROM public.nyc311_requests
  GROUP BY agency;


--
-- PostgreSQL database dump complete
--

\unrestrict eRlIkjnyy5SgO488U94FcEV65zbZXEIsG1bp2ax5K3Punw95H6cec8hgqOmyJV9

