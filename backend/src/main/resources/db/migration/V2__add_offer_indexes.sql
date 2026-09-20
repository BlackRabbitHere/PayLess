-- Merchant/provider lookup with verification filtering; expiry and refresh maintenance.
CREATE INDEX offer_merchant_verification_idx ON offer (merchant, verification_status);
CREATE INDEX offer_provider_idx ON offer (provider);
CREATE INDEX offer_last_verified_idx ON offer (last_verified_at);
CREATE INDEX offer_valid_until_idx ON offer (valid_until) WHERE valid_until IS NOT NULL;
CREATE INDEX scraper_run_request_idx ON scraper_run (request_id);
CREATE INDEX scraper_run_provider_completed_idx ON scraper_run (provider, completed_at DESC);
