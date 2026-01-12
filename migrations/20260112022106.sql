-- Create type messagebroker
CREATE TYPE "messagebroker" AS ENUM ('API', 'WHATSAPP');

-- Create column broker in table message
ALTER TABLE "message" ADD COLUMN "broker" "messagebroker" NOT NULL;
