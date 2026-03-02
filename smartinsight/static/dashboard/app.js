(() => {
    const tokenForm = document.getElementById("token-form");
    const uploadForm = document.getElementById("upload-form");
    const tokenStatus = document.getElementById("token-status");
    const uploadStatus = document.getElementById("upload-status");
    const kpiRevenue = document.getElementById("kpi-revenue");
    const kpiAverage = document.getElementById("kpi-average");
    const kpiRows = document.getElementById("kpi-rows");
    const segmentationOutput = document.getElementById("segmentation-output");
    const anomalyOutput = document.getElementById("anomaly-output");
    const forecastOutput = document.getElementById("forecast-output");
    const chartCanvas = document.getElementById("monthly-chart");

    let accessToken = window.localStorage.getItem("smartinsight_access_token") || "";
    let monthlyChart = null;
    const numberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

    const setStatus = (element, message, isSuccess) => {
        element.textContent = message;
        element.dataset.state = isSuccess ? "success" : "error";
    };

    const setNeutral = (element, message) => {
        element.textContent = message;
        element.dataset.state = "neutral";
    };

    const withLoading = async (buttonId, text, action) => {
        const button = document.getElementById(buttonId);
        if (!button) {
            return action();
        }
        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = text;
        try {
            return await action();
        } finally {
            button.disabled = false;
            button.textContent = originalText;
        }
    };

    const pretty = (value) => JSON.stringify(value, null, 2);

    const labelize = (key) =>
        key
            .replace(/_/g, " ")
            .replace(/\b\w/g, (char) => char.toUpperCase());

    const escapeHtml = (value) =>
        String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");

    const parseJsonString = (value) => {
        if (typeof value !== "string") {
            return value;
        }
        try {
            return JSON.parse(value);
        } catch {
            return value;
        }
    };

    const formatValue = (value) => {
        if (value === null || value === undefined || value === "") {
            return "-";
        }
        if (typeof value === "number") {
            return numberFormatter.format(Number(value));
        }
        if (typeof value === "object") {
            return JSON.stringify(value);
        }
        return String(value);
    };

    const normalizePayload = (payload) => {
        payload = parseJsonString(payload);

        if (
            payload &&
            typeof payload === "object" &&
            typeof payload.records === "string"
        ) {
            payload = {
                ...payload,
                records: parseJsonString(payload.records),
            };
        }

        if (Array.isArray(payload)) {
            return { rows: payload, meta: "" };
        }
        if (payload && typeof payload === "object" && Array.isArray(payload.records)) {
            const anomalyCount = payload.anomaly_count ?? payload.records.length;
            return {
                rows: payload.records,
                meta: `Anomaly Count: ${numberFormatter.format(Number(anomalyCount))}`,
            };
        }
        if (payload && typeof payload === "object") {
            return { rows: [payload], meta: "" };
        }
        return { rows: [], meta: "" };
    };

    const renderTable = (element, payload, options = {}) => {
        const { emptyMessage = "No records found." } = options;
        const { rows, meta } = normalizePayload(payload);

        if (!rows.length) {
            element.innerHTML = `<p class="table-empty">${escapeHtml(emptyMessage)}</p>`;
            return;
        }

        const objectRows = rows.map((row) =>
            row && typeof row === "object" && !Array.isArray(row) ? row : { value: row }
        );
        const columns = Array.from(
            objectRows.reduce((keys, row) => {
                Object.keys(row).forEach((key) => keys.add(key));
                return keys;
            }, new Set())
        );

        const headerHtml = columns
            .map((column) => `<th>${escapeHtml(labelize(column))}</th>`)
            .join("");
        const bodyHtml = objectRows
            .map(
                (row) =>
                    `<tr>${columns
                        .map((column) => `<td>${escapeHtml(formatValue(row[column]))}</td>`)
                        .join("")}</tr>`
            )
            .join("");

        element.innerHTML = `
            ${meta ? `<p class="result-meta">${escapeHtml(meta)}</p>` : ""}
            <div class="table-wrap">
                <table class="result-table">
                    <thead><tr>${headerHtml}</tr></thead>
                    <tbody>${bodyHtml}</tbody>
                </table>
            </div>
        `;
    };

    const renderError = (element, message) => {
        element.innerHTML = `<p class="table-error">${escapeHtml(message)}</p>`;
    };

    const authHeaders = () => {
        if (!accessToken) {
            throw new Error("Generate a JWT token first.");
        }
        return { Authorization: `Bearer ${accessToken}` };
    };

    const parseApiError = async (response) => {
        let payload = {};
        try {
            payload = await response.json();
        } catch {
            return `HTTP ${response.status}`;
        }
        if (payload.detail) {
            return payload.detail;
        }
        return pretty(payload);
    };

    const drawMonthlyChart = (monthlySales) => {
        const labels = Object.keys(monthlySales || {});
        const values = Object.values(monthlySales || {});
        if (monthlyChart) {
            monthlyChart.destroy();
        }
        monthlyChart = new Chart(chartCanvas, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Monthly Sales",
                        data: values,
                        tension: 0.34,
                        borderWidth: 2,
                        borderColor: "#22d3ee",
                        fill: true,
                        backgroundColor: "rgba(34, 211, 238, 0.18)",
                        pointRadius: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#dbeafe" } },
                },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.08)" } },
                    y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.08)" } },
                },
            },
        });
    };

    const fetchKpi = async () => {
        const response = await fetch("/api/analytics/kpi/", {
            headers: {
                "Content-Type": "application/json",
                ...authHeaders(),
            },
        });
        if (!response.ok) {
            throw new Error(await parseApiError(response));
        }
        const data = await response.json();
        kpiRevenue.textContent = numberFormatter.format(Number(data.total_revenue ?? 0));
        kpiAverage.textContent = numberFormatter.format(Number(data.avg_sales ?? 0));
        kpiRows.textContent = data.row_count ?? 0;
        drawMonthlyChart(data.monthly_sales || {});
    };

    tokenForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        try {
            await withLoading("token-form-button", "Authenticating...", async () => {
                const response = await fetch("/api/auth/token/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password }),
                });
                if (!response.ok) {
                    throw new Error(await parseApiError(response));
                }
                const data = await response.json();
                accessToken = data.access;
                window.localStorage.setItem("smartinsight_access_token", accessToken);
                setStatus(tokenStatus, "Token generated and saved in local storage.", true);
            });
        } catch (error) {
            setStatus(tokenStatus, error.message, false);
        }
    });

    uploadForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const fileInput = document.getElementById("dataset-file");
        if (!fileInput.files.length) {
            setStatus(uploadStatus, "Choose a CSV file first.", false);
            return;
        }

        try {
            await withLoading("upload-form-button", "Uploading...", async () => {
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                const response = await fetch("/api/data/upload/", {
                    method: "POST",
                    headers: {
                        ...authHeaders(),
                    },
                    body: formData,
                });
                if (!response.ok) {
                    throw new Error(await parseApiError(response));
                }
                const data = await response.json();
                setStatus(uploadStatus, data.message || "File uploaded.", true);
            });
        } catch (error) {
            setStatus(uploadStatus, error.message, false);
        }
    });

    document.getElementById("refresh-kpi").addEventListener("click", async () => {
        try {
            await withLoading("refresh-kpi", "Refreshing...", async () => fetchKpi());
            setNeutral(uploadStatus, "KPI refreshed successfully.");
        } catch (error) {
            setStatus(uploadStatus, error.message, false);
        }
    });

    document.getElementById("load-segmentation").addEventListener("click", async () => {
        try {
            await withLoading("load-segmentation", "Running...", async () => {
                const response = await fetch("/api/analytics/segment/", {
                    headers: { ...authHeaders() },
                });
                if (!response.ok) {
                    throw new Error(await parseApiError(response));
                }
                const data = await response.json();
                renderTable(segmentationOutput, data, {
                    emptyMessage: "No segmentation records found.",
                });
            });
        } catch (error) {
            renderError(segmentationOutput, error.message);
        }
    });

    document.getElementById("load-anomaly").addEventListener("click", async () => {
        try {
            await withLoading("load-anomaly", "Running...", async () => {
                const response = await fetch("/api/analytics/anomaly/", {
                    headers: { ...authHeaders() },
                });
                if (!response.ok) {
                    throw new Error(await parseApiError(response));
                }
                const data = await response.json();
                renderTable(anomalyOutput, data, {
                    emptyMessage: "No anomalies found in the uploaded dataset.",
                });
            });
        } catch (error) {
            renderError(anomalyOutput, error.message);
        }
    });

    document.getElementById("load-forecast").addEventListener("click", async () => {
        try {
            await withLoading("load-forecast", "Running...", async () => {
                const response = await fetch("/api/analytics/forecast/?periods=30", {
                    headers: { ...authHeaders() },
                });
                if (!response.ok) {
                    throw new Error(await parseApiError(response));
                }
                const data = await response.json();
                renderTable(forecastOutput, data, {
                    emptyMessage: "No forecast data was returned.",
                });
            });
        } catch (error) {
            renderError(forecastOutput, error.message);
        }
    });

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.transitionDelay = `${Math.min(240, Math.floor(Math.random() * 140))}ms`;
                    entry.target.classList.add("visible");
                }
            });
        },
        { threshold: 0.12 }
    );
    document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
})();
