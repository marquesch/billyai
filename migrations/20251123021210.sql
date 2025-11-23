-- Create "category" table
CREATE TABLE "category" (
 "id" serial NOT NULL,
 "name" character varying NOT NULL,
 "description" character varying NULL,
 PRIMARY KEY ("id")
);
-- Create "user" table
CREATE TABLE "user" (
 "id" serial NOT NULL,
 "phone_number" character varying NOT NULL,
 "name" character varying NULL,
 PRIMARY KEY ("id")
);
-- Create "bill" table
CREATE TABLE "bill" (
 "id" serial NOT NULL,
 "value" integer NOT NULL,
 "date" timestamp NOT NULL,
 "category_id" integer NULL,
 PRIMARY KEY ("id"),
 CONSTRAINT "bill_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);
