CREATE TABLE "aoi" (
    "id" uuid NOT NULL,
    "user_id" uuid,
    "geometry" json,
    "name" text,
    "description" text,
    "created_at" TIMESTAMP(6) without time zone,
    PRIMARY KEY ("id")
);

CREATE TABLE "user" (
    "id" uuid NOT NULL,
    "email" character varying(255),
    "password" character varying(255),
    "first_name" character varying(255),
    "last_name" character varying(255),
    "verified" boolean,
    "verify_secret" character varying(255),
    "created_at" TIMESTAMP(6) without time zone,
    "reset_token" text,
    "reset_token_expiry" TIMESTAMP(6) without time zone,
    PRIMARY KEY ("id")
);

CREATE TABLE "task" (
    "id" uuid NOT NULL,
    "user_id" uuid,
    "aoi_id" uuid,
    "name" text,
    "created_at" TIMESTAMP(6) without time zone,
    "status" text,
    "is_public" boolean,
    PRIMARY KEY ("id")
);

CREATE TABLE "task_processes" (
    "task_id" uuid NOT NULL,
    "gee_task_id" text,
    "gee_current_status" text,
    "forced_action_taken" text,
    "last_updated" TIMESTAMP(6) without time zone,
    PRIMARY KEY ("task_id")
);