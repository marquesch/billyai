-- Modify "bill" table
ALTER TABLE "bill" ALTER COLUMN "value" TYPE double precision, ADD COLUMN "user_id" integer NOT NULL, ADD CONSTRAINT "bill_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
