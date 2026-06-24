create table BATCH_JOB_INSTANCE (
    JOB_INSTANCE_ID bigint not null primary key,
    VERSION bigint,
    JOB_NAME varchar(100) not null,
    JOB_KEY varchar(32) not null,
    constraint JOB_INST_UN unique (JOB_NAME, JOB_KEY)
);

create table BATCH_JOB_EXECUTION (
    JOB_EXECUTION_ID bigint not null primary key,
    VERSION bigint,
    JOB_INSTANCE_ID bigint not null,
    CREATE_TIME datetime(6) not null,
    START_TIME datetime(6),
    END_TIME datetime(6),
    STATUS varchar(10),
    EXIT_CODE varchar(2500),
    EXIT_MESSAGE varchar(2500),
    LAST_UPDATED datetime(6),
    constraint JOB_INST_EXEC_FK foreign key (JOB_INSTANCE_ID)
        references BATCH_JOB_INSTANCE (JOB_INSTANCE_ID)
);

create table BATCH_JOB_EXECUTION_PARAMS (
    JOB_EXECUTION_ID bigint not null,
    PARAMETER_NAME varchar(100) not null,
    PARAMETER_TYPE varchar(100) not null,
    PARAMETER_VALUE varchar(2500),
    IDENTIFYING char(1) not null,
    constraint JOB_EXEC_PARAMS_FK foreign key (JOB_EXECUTION_ID)
        references BATCH_JOB_EXECUTION (JOB_EXECUTION_ID)
);

create table BATCH_STEP_EXECUTION (
    STEP_EXECUTION_ID bigint not null primary key,
    VERSION bigint not null,
    STEP_NAME varchar(100) not null,
    JOB_EXECUTION_ID bigint not null,
    CREATE_TIME datetime(6) not null,
    START_TIME datetime(6),
    END_TIME datetime(6),
    STATUS varchar(10),
    COMMIT_COUNT bigint,
    READ_COUNT bigint,
    FILTER_COUNT bigint,
    WRITE_COUNT bigint,
    READ_SKIP_COUNT bigint,
    WRITE_SKIP_COUNT bigint,
    PROCESS_SKIP_COUNT bigint,
    ROLLBACK_COUNT bigint,
    EXIT_CODE varchar(2500),
    EXIT_MESSAGE varchar(2500),
    LAST_UPDATED datetime(6),
    constraint JOB_EXEC_STEP_FK foreign key (JOB_EXECUTION_ID)
        references BATCH_JOB_EXECUTION (JOB_EXECUTION_ID)
);

create table BATCH_STEP_EXECUTION_CONTEXT (
    STEP_EXECUTION_ID bigint not null primary key,
    SHORT_CONTEXT varchar(2500) not null,
    SERIALIZED_CONTEXT text,
    constraint STEP_EXEC_CTX_FK foreign key (STEP_EXECUTION_ID)
        references BATCH_STEP_EXECUTION (STEP_EXECUTION_ID)
);

create table BATCH_JOB_EXECUTION_CONTEXT (
    JOB_EXECUTION_ID bigint not null primary key,
    SHORT_CONTEXT varchar(2500) not null,
    SERIALIZED_CONTEXT text,
    constraint JOB_EXEC_CTX_FK foreign key (JOB_EXECUTION_ID)
        references BATCH_JOB_EXECUTION (JOB_EXECUTION_ID)
);

create table BATCH_STEP_EXECUTION_SEQ (
    ID bigint not null
);

insert into BATCH_STEP_EXECUTION_SEQ values (0);

create table BATCH_JOB_EXECUTION_SEQ (
    ID bigint not null
);

insert into BATCH_JOB_EXECUTION_SEQ values (0);

create table BATCH_JOB_SEQ (
    ID bigint not null
);

insert into BATCH_JOB_SEQ values (0);

create table market_data_sources (
    id varchar(80) not null,
    title varchar(120) not null,
    label varchar(120) not null,
    provider varchar(80) not null,
    source_url varchar(1000) not null,
    category varchar(40) not null,
    tone varchar(40) not null,
    enabled boolean not null,
    last_checked_at datetime(6),
    stale boolean not null,
    status varchar(40) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id)
);

create table market_data_schedules (
    id varchar(140) not null,
    source_id varchar(80) not null,
    schedule_date date not null,
    title varchar(160) not null,
    category varchar(40) not null,
    source_title varchar(120) not null,
    summary varchar(500) not null,
    source_url varchar(1000) not null,
    tone varchar(40) not null,
    provider varchar(80) not null,
    status varchar(40) not null,
    data_status varchar(30) not null,
    stale boolean not null,
    last_checked_at datetime(6),
    as_of date,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_market_data_schedules_source_date_title unique (source_id, schedule_date, title),
    constraint fk_market_data_schedules_source foreign key (source_id)
        references market_data_sources (id)
);

create index idx_market_data_schedules_month on market_data_schedules (schedule_date);
create index idx_market_data_schedules_source on market_data_schedules (source_id);
