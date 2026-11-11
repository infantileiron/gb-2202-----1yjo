-- 002 补报修订（dataset supplements）。
-- 新数据库由 SQLAlchemy Base.metadata.create_all 自动建立以下结构；
-- 存量 MySQL 8 部署在备份后执行本脚本，不删除任何既有数据。
-- 规则：原始事件视为修订0；补报带 revision>=1，同票同里程碑取较新修订；
-- 迟到旧记录不覆盖、重复投递不新增、同修订号内容冲突整批拒收。

ALTER TABLE datasets
  ADD COLUMN version INT NOT NULL DEFAULT 0,
  ADD COLUMN revisions JSON NULL;
-- 存量行的 revisions 归一化为空数组（JSON列默认值在MySQL中不能直接写字面量）。
UPDATE datasets SET revisions = JSON_ARRAY() WHERE revisions IS NULL;

CREATE TABLE dataset_supplements (
  id VARCHAR(36) NOT NULL PRIMARY KEY,
  created_at DATETIME NOT NULL,
  dataset_id VARCHAR(36) NOT NULL,
  seq INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'accepted',
  note VARCHAR(300) NOT NULL DEFAULT '',
  row_count INT NOT NULL DEFAULT 0,
  accepted_count INT NOT NULL DEFAULT 0,
  ignored_count INT NOT NULL DEFAULT 0,
  conflict_count INT NOT NULL DEFAULT 0,
  decisions JSON NULL,
  INDEX ix_dataset_supplements_dataset_id (dataset_id)
);
UPDATE dataset_supplements SET decisions = JSON_ARRAY() WHERE decisions IS NULL;

-- 运行记录钉住入队时的数据版本与事件快照，保证排队/历史运行保留原口径。
ALTER TABLE runs
  ADD COLUMN dataset_version INT NOT NULL DEFAULT 0,
  ADD COLUMN dataset_snapshot JSON NULL;
UPDATE runs SET dataset_snapshot = JSON_ARRAY() WHERE dataset_snapshot IS NULL;
