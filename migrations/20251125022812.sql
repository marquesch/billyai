-- Create "tenant" table
CREATE TABLE "tenant" (
 "id" serial NOT NULL,
 PRIMARY KEY ("id")
);
-- Rename a column from "user_id" to "tenant_id"
ALTER TABLE "bill" RENAME COLUMN "user_id" TO "tenant_id";
-- Modify "bill" table
ALTER TABLE "bill" DROP CONSTRAINT "bill_user_id_fkey", ADD CONSTRAINT "bill_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenant" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
-- Modify "category" table
ALTER TABLE "category" ADD COLUMN "tenant_id" integer NOT NULL, ADD CONSTRAINT "category_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenant" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
-- Modify "user" table
ALTER TABLE "user" ADD COLUMN "tenant_id" integer NOT NULL, ADD CONSTRAINT "user_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenant" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
