-- Modify "category" table
ALTER TABLE "category" ADD CONSTRAINT "category_name_tenant_id_key" UNIQUE ("name", "tenant_id");
-- Create index "ix_user_phone_number" to table: "user"
CREATE UNIQUE INDEX "ix_user_phone_number" ON "user" ("phone_number");
