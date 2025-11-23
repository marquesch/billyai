-- Modify "category" table
ALTER TABLE "category" ADD COLUMN "user_id" integer NULL, ADD CONSTRAINT "category_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
