-- Схема базы данных рекрутинговой ИС «UnitHire»
-- Сгенерировано из миграций Django (python manage.py sqlmigrate).
-- В продакшене используется PostgreSQL; типы приведены к синтаксису СУБД.

BEGIN;
--
-- Create model User
--
CREATE TABLE "core_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "first_name" varchar(150) NOT NULL, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "patronymic" varchar(100) NOT NULL, "role" varchar(20) NOT NULL, "phone" varchar(20) NOT NULL, "position" varchar(120) NOT NULL, "created_at" datetime NOT NULL);
--
-- Create model Application
--
CREATE TABLE "core_application" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "cover_letter" text NOT NULL, "comment" text NOT NULL, "applied_at" datetime NOT NULL, "updated_at" datetime NOT NULL);
--
-- Create model Article
--
CREATE TABLE "core_article" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "slug" varchar(210) NOT NULL UNIQUE, "summary" varchar(300) NOT NULL, "body" text NOT NULL, "author_name" varchar(120) NOT NULL, "published_at" date NOT NULL, "is_published" bool NOT NULL);
--
-- Create model Candidate
--
CREATE TABLE "core_candidate" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "last_name" varchar(80) NOT NULL, "first_name" varchar(80) NOT NULL, "patronymic" varchar(80) NOT NULL, "email" varchar(254) NOT NULL, "phone" varchar(20) NOT NULL, "city" varchar(80) NOT NULL, "desired_salary" integer unsigned NOT NULL CHECK ("desired_salary" >= 0), "experience_years" decimal NOT NULL, "grade" varchar(20) NOT NULL, "summary" text NOT NULL, "is_archived" bool NOT NULL, "created_at" datetime NOT NULL);
--
-- Create model Department
--
CREATE TABLE "core_department" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(120) NOT NULL UNIQUE, "head" varchar(120) NOT NULL, "headcount_plan" integer unsigned NOT NULL CHECK ("headcount_plan" >= 0), "description" text NOT NULL);
--
-- Create model Feedback
--
CREATE TABLE "core_feedback" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(120) NOT NULL, "email" varchar(254) NOT NULL, "phone" varchar(20) NOT NULL, "subject" varchar(160) NOT NULL, "message" text NOT NULL, "is_processed" bool NOT NULL, "created_at" datetime NOT NULL);
--
-- Create model Skill
--
CREATE TABLE "core_skill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(80) NOT NULL UNIQUE, "category" varchar(20) NOT NULL, "description" varchar(255) NOT NULL);
--
-- Create model Source
--
CREATE TABLE "core_source" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(120) NOT NULL UNIQUE, "kind" varchar(60) NOT NULL, "cost_per_contact" decimal NOT NULL, "is_active" bool NOT NULL);
--
-- Create model Stage
--
CREATE TABLE "core_stage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(80) NOT NULL UNIQUE, "order" smallint unsigned NOT NULL UNIQUE CHECK ("order" >= 0), "description" varchar(255) NOT NULL, "is_terminal" bool NOT NULL);
--
-- Create model Vacancy
--
CREATE TABLE "core_vacancy" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(150) NOT NULL, "grade" varchar(20) NOT NULL, "salary_min" integer unsigned NOT NULL CHECK ("salary_min" >= 0), "salary_max" integer unsigned NOT NULL CHECK ("salary_max" >= 0), "status" varchar(20) NOT NULL, "description" text NOT NULL, "city" varchar(80) NOT NULL, "is_remote" bool NOT NULL, "opened_at" date NOT NULL, "planned_close" date NULL, "closed_at" date NULL, "department_id" bigint NOT NULL REFERENCES "core_department" ("id") DEFERRABLE INITIALLY DEFERRED, "recruiter_id" bigint NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model VacancySkill
--
CREATE TABLE "core_vacancyskill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "is_required" bool NOT NULL, "skill_id" bigint NOT NULL REFERENCES "core_skill" ("id") DEFERRABLE INITIALLY DEFERRED, "vacancy_id" bigint NOT NULL REFERENCES "core_vacancy" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Add field required_skills to vacancy
--
CREATE TABLE "new__core_vacancy" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(150) NOT NULL, "grade" varchar(20) NOT NULL, "salary_min" integer unsigned NOT NULL CHECK ("salary_min" >= 0), "salary_max" integer unsigned NOT NULL CHECK ("salary_max" >= 0), "status" varchar(20) NOT NULL, "description" text NOT NULL, "city" varchar(80) NOT NULL, "is_remote" bool NOT NULL, "opened_at" date NOT NULL, "planned_close" date NULL, "closed_at" date NULL, "department_id" bigint NOT NULL REFERENCES "core_department" ("id") DEFERRABLE INITIALLY DEFERRED, "recruiter_id" bigint NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_vacancy" ("id", "title", "grade", "salary_min", "salary_max", "status", "description", "city", "is_remote", "opened_at", "planned_close", "closed_at", "department_id", "recruiter_id") SELECT "id", "title", "grade", "salary_min", "salary_max", "status", "description", "city", "is_remote", "opened_at", "planned_close", "closed_at", "department_id", "recruiter_id" FROM "core_vacancy";
DROP TABLE "core_vacancy";
ALTER TABLE "new__core_vacancy" RENAME TO "core_vacancy";
CREATE INDEX "core_vacancyskill_skill_id_6abe898d" ON "core_vacancyskill" ("skill_id");
CREATE INDEX "core_vacancyskill_vacancy_id_e8e519bd" ON "core_vacancyskill" ("vacancy_id");
CREATE INDEX "core_vacancy_department_id_96eda9ac" ON "core_vacancy" ("department_id");
CREATE INDEX "core_vacancy_recruiter_id_39cd248f" ON "core_vacancy" ("recruiter_id");
--
-- Create model ResumeFile
--
CREATE TABLE "core_resumefile" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "file" varchar(100) NOT NULL, "title" varchar(150) NOT NULL, "uploaded_at" datetime NOT NULL, "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Offer
--
CREATE TABLE "core_offer" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "salary" integer unsigned NOT NULL CHECK ("salary" >= 0), "start_date" date NULL, "status" varchar(20) NOT NULL, "sent_at" date NOT NULL, "comment" varchar(255) NOT NULL, "application_id" bigint NOT NULL UNIQUE REFERENCES "core_application" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Interview
--
CREATE TABLE "core_interview" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "kind" varchar(20) NOT NULL, "scheduled_at" datetime NOT NULL, "result" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "notes" text NOT NULL, "application_id" bigint NOT NULL REFERENCES "core_application" ("id") DEFERRABLE INITIALLY DEFERRED, "interviewer_id" bigint NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Evaluation
--
CREATE TABLE "core_evaluation" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "criterion" varchar(120) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "comment" varchar(255) NOT NULL, "interview_id" bigint NOT NULL REFERENCES "core_interview" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model CandidateSkill
--
CREATE TABLE "core_candidateskill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "level" smallint unsigned NOT NULL CHECK ("level" >= 0), "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED, "skill_id" bigint NOT NULL REFERENCES "core_skill" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Add field skills to candidate
--
CREATE TABLE "new__core_candidate" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "last_name" varchar(80) NOT NULL, "first_name" varchar(80) NOT NULL, "patronymic" varchar(80) NOT NULL, "email" varchar(254) NOT NULL, "phone" varchar(20) NOT NULL, "city" varchar(80) NOT NULL, "desired_salary" integer unsigned NOT NULL CHECK ("desired_salary" >= 0), "experience_years" decimal NOT NULL, "grade" varchar(20) NOT NULL, "summary" text NOT NULL, "is_archived" bool NOT NULL, "created_at" datetime NOT NULL);
INSERT INTO "new__core_candidate" ("id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at") SELECT "id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at" FROM "core_candidate";
DROP TABLE "core_candidate";
ALTER TABLE "new__core_candidate" RENAME TO "core_candidate";
CREATE INDEX "core_resumefile_candidate_id_0526bad3" ON "core_resumefile" ("candidate_id");
CREATE INDEX "core_interview_application_id_100d603b" ON "core_interview" ("application_id");
CREATE INDEX "core_interview_interviewer_id_c0621c0f" ON "core_interview" ("interviewer_id");
CREATE INDEX "core_evaluation_interview_id_d1c987bb" ON "core_evaluation" ("interview_id");
CREATE INDEX "core_candidateskill_candidate_id_3c11287a" ON "core_candidateskill" ("candidate_id");
CREATE INDEX "core_candidateskill_skill_id_5c4b73af" ON "core_candidateskill" ("skill_id");
--
-- Add field source to candidate
--
CREATE TABLE "new__core_candidate" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "last_name" varchar(80) NOT NULL, "first_name" varchar(80) NOT NULL, "patronymic" varchar(80) NOT NULL, "email" varchar(254) NOT NULL, "phone" varchar(20) NOT NULL, "city" varchar(80) NOT NULL, "desired_salary" integer unsigned NOT NULL CHECK ("desired_salary" >= 0), "experience_years" decimal NOT NULL, "grade" varchar(20) NOT NULL, "summary" text NOT NULL, "is_archived" bool NOT NULL, "created_at" datetime NOT NULL, "source_id" bigint NOT NULL REFERENCES "core_source" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_candidate" ("id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at", "source_id") SELECT "id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at", NULL FROM "core_candidate";
DROP TABLE "core_candidate";
ALTER TABLE "new__core_candidate" RENAME TO "core_candidate";
CREATE INDEX "core_candidate_source_id_c0597250" ON "core_candidate" ("source_id");
--
-- Add field user to candidate
--
CREATE TABLE "new__core_candidate" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "last_name" varchar(80) NOT NULL, "first_name" varchar(80) NOT NULL, "patronymic" varchar(80) NOT NULL, "email" varchar(254) NOT NULL, "phone" varchar(20) NOT NULL, "city" varchar(80) NOT NULL, "desired_salary" integer unsigned NOT NULL CHECK ("desired_salary" >= 0), "experience_years" decimal NOT NULL, "grade" varchar(20) NOT NULL, "summary" text NOT NULL, "is_archived" bool NOT NULL, "created_at" datetime NOT NULL, "source_id" bigint NOT NULL REFERENCES "core_source" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" bigint NULL UNIQUE REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_candidate" ("id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at", "source_id", "user_id") SELECT "id", "last_name", "first_name", "patronymic", "email", "phone", "city", "desired_salary", "experience_years", "grade", "summary", "is_archived", "created_at", "source_id", NULL FROM "core_candidate";
DROP TABLE "core_candidate";
ALTER TABLE "new__core_candidate" RENAME TO "core_candidate";
CREATE INDEX "core_candidate_source_id_c0597250" ON "core_candidate" ("source_id");
--
-- Add field candidate to application
--
CREATE TABLE "new__core_application" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "cover_letter" text NOT NULL, "comment" text NOT NULL, "applied_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_application" ("id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id") SELECT "id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", NULL FROM "core_application";
DROP TABLE "core_application";
ALTER TABLE "new__core_application" RENAME TO "core_application";
CREATE INDEX "core_application_candidate_id_0dc16e83" ON "core_application" ("candidate_id");
--
-- Add field stage to application
--
CREATE TABLE "new__core_application" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "cover_letter" text NOT NULL, "comment" text NOT NULL, "applied_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED, "stage_id" bigint NOT NULL REFERENCES "core_stage" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_application" ("id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", "stage_id") SELECT "id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", NULL FROM "core_application";
DROP TABLE "core_application";
ALTER TABLE "new__core_application" RENAME TO "core_application";
CREATE INDEX "core_application_candidate_id_0dc16e83" ON "core_application" ("candidate_id");
CREATE INDEX "core_application_stage_id_8cce302c" ON "core_application" ("stage_id");
--
-- Add field vacancy to application
--
CREATE TABLE "new__core_application" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "cover_letter" text NOT NULL, "comment" text NOT NULL, "applied_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED, "stage_id" bigint NOT NULL REFERENCES "core_stage" ("id") DEFERRABLE INITIALLY DEFERRED, "vacancy_id" bigint NOT NULL REFERENCES "core_vacancy" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__core_application" ("id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", "stage_id", "vacancy_id") SELECT "id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", "stage_id", NULL FROM "core_application";
DROP TABLE "core_application";
ALTER TABLE "new__core_application" RENAME TO "core_application";
CREATE INDEX "core_application_candidate_id_0dc16e83" ON "core_application" ("candidate_id");
CREATE INDEX "core_application_stage_id_8cce302c" ON "core_application" ("stage_id");
CREATE INDEX "core_application_vacancy_id_ab7e8359" ON "core_application" ("vacancy_id");
--
-- Add field department to user
--
ALTER TABLE "core_user" ADD COLUMN "department_id" bigint NULL REFERENCES "core_department" ("id") DEFERRABLE INITIALLY DEFERRED;
--
-- Add field groups to user
--
CREATE TABLE "core_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Add field user_permissions to user
--
CREATE TABLE "core_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" bigint NOT NULL REFERENCES "core_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create constraint uniq_vacancy_skill on model vacancyskill
--
CREATE TABLE "new__core_vacancyskill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "is_required" bool NOT NULL, "skill_id" bigint NOT NULL REFERENCES "core_skill" ("id") DEFERRABLE INITIALLY DEFERRED, "vacancy_id" bigint NOT NULL REFERENCES "core_vacancy" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uniq_vacancy_skill" UNIQUE ("vacancy_id", "skill_id"));
INSERT INTO "new__core_vacancyskill" ("id", "is_required", "skill_id", "vacancy_id") SELECT "id", "is_required", "skill_id", "vacancy_id" FROM "core_vacancyskill";
DROP TABLE "core_vacancyskill";
ALTER TABLE "new__core_vacancyskill" RENAME TO "core_vacancyskill";
CREATE INDEX "core_user_department_id_172c32d3" ON "core_user" ("department_id");
CREATE UNIQUE INDEX "core_user_groups_user_id_group_id_c82fcad1_uniq" ON "core_user_groups" ("user_id", "group_id");
CREATE INDEX "core_user_groups_user_id_70b4d9b8" ON "core_user_groups" ("user_id");
CREATE INDEX "core_user_groups_group_id_fe8c697f" ON "core_user_groups" ("group_id");
CREATE UNIQUE INDEX "core_user_user_permissions_user_id_permission_id_73ea0daa_uniq" ON "core_user_user_permissions" ("user_id", "permission_id");
CREATE INDEX "core_user_user_permissions_user_id_085123d3" ON "core_user_user_permissions" ("user_id");
CREATE INDEX "core_user_user_permissions_permission_id_35ccf601" ON "core_user_user_permissions" ("permission_id");
CREATE INDEX "core_vacancyskill_skill_id_6abe898d" ON "core_vacancyskill" ("skill_id");
CREATE INDEX "core_vacancyskill_vacancy_id_e8e519bd" ON "core_vacancyskill" ("vacancy_id");
--
-- Create index core_vacanc_status_c49e84_idx on field(s) status of model vacancy
--
CREATE INDEX "core_vacanc_status_c49e84_idx" ON "core_vacancy" ("status");
--
-- Create constraint uniq_candidate_skill on model candidateskill
--
CREATE TABLE "new__core_candidateskill" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "level" smallint unsigned NOT NULL CHECK ("level" >= 0), "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED, "skill_id" bigint NOT NULL REFERENCES "core_skill" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uniq_candidate_skill" UNIQUE ("candidate_id", "skill_id"));
INSERT INTO "new__core_candidateskill" ("id", "level", "candidate_id", "skill_id") SELECT "id", "level", "candidate_id", "skill_id" FROM "core_candidateskill";
DROP TABLE "core_candidateskill";
ALTER TABLE "new__core_candidateskill" RENAME TO "core_candidateskill";
CREATE INDEX "core_candidateskill_candidate_id_3c11287a" ON "core_candidateskill" ("candidate_id");
CREATE INDEX "core_candidateskill_skill_id_5c4b73af" ON "core_candidateskill" ("skill_id");
--
-- Create index core_candid_last_na_742bf6_idx on field(s) last_name, first_name of model candidate
--
CREATE INDEX "core_candid_last_na_742bf6_idx" ON "core_candidate" ("last_name", "first_name");
--
-- Create constraint uniq_candidate_vacancy on model application
--
CREATE TABLE "new__core_application" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "score" smallint unsigned NOT NULL CHECK ("score" >= 0), "cover_letter" text NOT NULL, "comment" text NOT NULL, "applied_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "candidate_id" bigint NOT NULL REFERENCES "core_candidate" ("id") DEFERRABLE INITIALLY DEFERRED, "stage_id" bigint NOT NULL REFERENCES "core_stage" ("id") DEFERRABLE INITIALLY DEFERRED, "vacancy_id" bigint NOT NULL REFERENCES "core_vacancy" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uniq_candidate_vacancy" UNIQUE ("candidate_id", "vacancy_id"));
INSERT INTO "new__core_application" ("id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", "stage_id", "vacancy_id") SELECT "id", "status", "score", "cover_letter", "comment", "applied_at", "updated_at", "candidate_id", "stage_id", "vacancy_id" FROM "core_application";
DROP TABLE "core_application";
ALTER TABLE "new__core_application" RENAME TO "core_application";
CREATE INDEX "core_application_candidate_id_0dc16e83" ON "core_application" ("candidate_id");
CREATE INDEX "core_application_stage_id_8cce302c" ON "core_application" ("stage_id");
CREATE INDEX "core_application_vacancy_id_ab7e8359" ON "core_application" ("vacancy_id");
COMMIT;
