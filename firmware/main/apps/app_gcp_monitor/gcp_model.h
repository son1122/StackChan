/*
 * SPDX-FileCopyrightText: 2026 M5Stack Technology CO LTD
 *
 * SPDX-License-Identifier: MIT
 */
#pragma once
#include <string>
#include <cstdint>

namespace gcp_monitor {

struct GcpBilling {
    float mtd_usd = 128.45f;
    float today_usd = 8.20f;
    float budget_pct = 42.8f;
};

struct GkeStatus {
    std::string status = "ok";
    int nodes_up = 3;
    int nodes_total = 3;
    int pods_running = 28;
    int pods_failed = 0;
    float cpu_pct = 38.0f;
    float ram_pct = 62.4f;
};

struct VmStatus {
    std::string status = "ok";
    int instances_running = 4;
    int instances_total = 4;
    float avg_cpu_pct = 22.5f;
};

struct CloudRunStatus {
    std::string status = "ok";
    int services_count = 6;
    float req_per_sec = 45.2f;
    float error_5xx_rate = 0.0f;
};

struct CloudSqlStatus {
    std::string status = "ok";
    int instances_up = 2;
    float cpu_pct = 28.0f;
    float storage_pct = 48.5f;
    int connections = 36;
};

struct BigQueryStatus {
    std::string status = "ok";
    int slot_usage = 12;
    float today_gb_billed = 145.2f;
    int failed_queries_24h = 0;
};

struct GcpTelemetry {
    std::string overall_status = "ok"; // "ok", "warning", "critical"
    int incident_count = 0;
    uint32_t last_updated_time = 0;
    std::string active_alert_msg = "";
    GcpBilling billing;
    GkeStatus gke;
    VmStatus vm;
    CloudRunStatus cloud_run;
    CloudSqlStatus cloud_sql;
    BigQueryStatus bigquery;
};

} // namespace gcp_monitor
