-- Create enum type "messageauthor"
CREATE TYPE "messageauthor" AS ENUM ('USER', 'BILLY', 'SYSTEM');
-- Create "message" table
CREATE TABLE "message" (
 "id" serial NOT NULL,
 "body" character varying NOT NULL,
 "author" "messageauthor" NOT NULL,
 "timestamp" timestamp NOT NULL,
 "external_message_id" character varying NULL,
 "user_id" integer NOT NULL,
 "tenant_id" integer NOT NULL,
 PRIMARY KEY ("id"),
 CONSTRAINT "message_external_message_id_key" UNIQUE ("external_message_id"),
 CONSTRAINT "message_tenant_id_fkey" FOREIGN KEY ("tenant_id") REFERENCES "tenant" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
 CONSTRAINT "message_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);
