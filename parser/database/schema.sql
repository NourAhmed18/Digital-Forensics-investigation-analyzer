BEGIN TRANSACTION;
CREATE TABLE "Artifact" (
    "artifactID" INTEGER PRIMARY KEY AUTOINCREMENT,
    "evidenceID" INTEGER,
    "artifact_type" TEXT,
    "original_timestamp" TEXT,
    "original_timezone" TEXT,
    "timestamp_utc" TEXT,
    "event_description" TEXT,
    "raw_record" TEXT,
    "parsed_at" TEXT,
    FOREIGN KEY ("evidenceID")
        REFERENCES "Evidence_File"("evidenceID")
);
CREATE TABLE "Browser_History" (
    "artifactID" INTEGER NOT NULL,
    "browser_name" TEXT,
    "profile_name" TEXT,
    "record_type" TEXT,
    "url" TEXT,
    "page_title" TEXT,
    "visit_count" INTEGER,
    "visited_at" TEXT,
    "download_path" TEXT,
    "download_started_at" TEXT,
    "mime_type" TEXT,
    "file_size" INTEGER,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
CREATE TABLE "Case" (
	"caseID"	TEXT NOT NULL,
	"case_name"	TEXT,
	"description"	TEXT,
	"hostname"	TEXT,
	"os_name"	TEXT,
	"os_version"	TEXT,
	"created_at"	TEXT,
	"status"	TEXT,
	PRIMARY KEY("caseID")
);
CREATE TABLE "Collector_Metadata" (
    "artifactID" INTEGER NOT NULL,
    "collector_version" TEXT,
    "schema_version" TEXT,
    "hostname" TEXT,
    "os_name" TEXT,
    "os_version" TEXT,
    "username" TEXT,
    "privilege_level" TEXT,
    "check_method" TEXT,
    "collection_start" TEXT,
    "collection_end" TEXT,
    "collected_at_utc" TEXT,
    "collector_status" TEXT,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
CREATE TABLE "Evidence_File" (
	"evidenceID"	INTEGER,
	"caseID"	TEXT,
	"file_name"	TEXT,
	"original_path"	TEXT,
	"stored_path"	TEXT,
	"file_type"	TEXT,
	"file_size"	INTEGER,
	"sha256_hash"	TEXT,
	"source_module"	TEXT,
	"acquisition_tool"	TEXT,
	"acquired_at"	TEXT,
	"timezone"	TEXT,
	"integrity_status"	TEXT,
	PRIMARY KEY("evidenceID" AUTOINCREMENT),
	FOREIGN KEY("caseID") REFERENCES "Case"("caseID")
);
CREATE TABLE "File_Event" (
    "artifactID" INTEGER NOT NULL,
    "action" TEXT,
    "file_path" TEXT,
    "file_sha256" TEXT,
    "file_size" INTEGER,
    "actor_process_id" INTEGER,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
CREATE TABLE "Network_Connection" (
    "artifactID" INTEGER NOT NULL,
    "protocol" TEXT,
    "local_ip" TEXT,
    "local_port" INTEGER,
    "remote_ip" TEXT,
    "remote_port" INTEGER,
    "connection_state" TEXT,
    "process_pid" INTEGER,
    "process_name" TEXT,
    "is_listening" INTEGER,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
CREATE TABLE "Process" (
    "artifactID" INTEGER NOT NULL,
    "pid" INTEGER,
    "parent_pid" INTEGER,
    "process_name" TEXT,
    "executable_path" TEXT,
    "command_line" TEXT,
    "username" TEXT,
    "status" TEXT,
    "start_time" TEXT,
    "end_time" TEXT,
    "executable_sha256" TEXT,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
CREATE TABLE "System_Event" (
    "artifactID" INTEGER NOT NULL,
    "event_source" TEXT,
    "event_code" TEXT,
    "event_level" TEXT,
    "hostname" TEXT,
    "username" TEXT,
    "message" TEXT,
    PRIMARY KEY ("artifactID"),
    FOREIGN KEY ("artifactID")
        REFERENCES "Artifact"("artifactID")
);
COMMIT;