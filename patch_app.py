import sys
import re
from pathlib import Path

app_path = Path('dashboard/js/app.js')
content = app_path.read_text(encoding='utf-8')

# Remove the old fetchLiveCSTC function as it's no longer needed
content = re.sub(r'async function fetchLiveCSTC.*?\}\n    \}', '', content, flags=re.DOTALL)

# Replace the calls in updateDashboardView
content = content.replace('''        if (activeSubTab === 'cstc') {
            renderCSTCTable();
        } else if (activeSubTab === 'chart') {
            renderFinancialCharts();
        } else {
            renderTable();
        }''', '''        if (activeSubTab === 'cstc' || activeSubTab === 'chart') {
            renderFinancialTab(currentTicker);
        } else {
            renderTable();
        }''')

# Now replace the bodies of renderCSTCTable and renderFinancialCharts
# Find the start of YUANTA FINANCIAL RATIOS renderer
start_idx = content.find('// YUANTA FINANCIAL RATIOS')
end_idx = content.find('function populateTickers', start_idx)

new_code = '''// =========================================================
    // FINANCIAL TAB (NEW ARCHITECTURE)
    // =========================================================
    async function loadFinancialData(stockCode) {
        const url = `${APP_CONFIG.STATIC_BASE_URL}/financials/${stockCode}.json`;
        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        } catch (err) {
            console.error(`Failed to load financials for ${stockCode}:`, err);
            return null;
        }
    }

    async function renderFinancialTab(stockCode) {
        tableHead.innerHTML = `<tr><th>Báo cáo tài chính & Phân tích cơ bản</th></tr>`;
        tableBody.innerHTML = `<tr><td style="text-align: center; padding: 2rem;">Đang tải dữ liệu BCTC...</td></tr>`;

        const data = await loadFinancialData(stockCode);
        if (!data) {
            tableBody.innerHTML = `<tr><td style="text-align: center; padding: 2rem; color: var(--danger);">Không có dữ liệu BCTC cho ${stockCode}</td></tr>`;
            return;
        }

        let html = '<div style="padding: 1.5rem; display: flex; flex-direction: column; gap: 2rem;">';

        // 1. Quick Ratios
        if (data.quick_ratios) {
            html += `<div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                <h3 style="margin-top:0; margin-bottom: 1rem; color: var(--accent);">Chỉ số định giá cơ bản</h3>
                <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">`;
            for (const [key, vals] of Object.entries(data.quick_ratios)) {
                if (vals && vals.length > 0 && vals[0] !== null) {
                    html += `<div style="background: var(--bg-main); padding: 1rem; border-radius: 8px; flex: 1; min-width: 120px; text-align: center;">
                        <div style="color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase;">${key}</div>
                        <div style="font-size: 1.5rem; font-weight: bold; margin-top: 0.5rem;">${vals[0]}</div>
                    </div>`;
                }
            }
            html += `</div></div>`;
        }

        // 2. AI Fundamental Analysis
        if (data.ai_fundamental) {
            html += `<div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                <h3 style="margin-top:0; margin-bottom: 1rem; color: #9c27b0;">Phân tích AI Fundamental (Mô hình: ${data.ai_fundamental.model})</h3>
                <div style="line-height: 1.6;">`;
            
            for (const [key, text] of Object.entries(data.ai_fundamental)) {
                if (key !== 'model' && key !== 'generated_at') {
                    const title = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
                    html += `<div><strong>${title}:</strong> ${text}</div><br>`;
                }
            }
            html += `</div></div>`;
        }

        // Helper to render table
        const renderTableHTML = (title, items, periods) => {
            if (!items || items.length === 0) return '';
            let t = `<div style="background: var(--bg-card); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color);">
                <h3 style="margin-top:0; margin-bottom: 1rem; color: var(--accent);">${title}</h3>
                <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead><tr>
                        <th style="text-align: left; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">Chỉ tiêu</th>`;
            for (const p of periods) {
                t += `<th style="text-align: right; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">${p}</th>`;
            }
            t += `</tr></thead><tbody>`;
            for (const item of items) {
                t += `<tr><td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); color: var(--text-main); font-weight: 500;">${item.name_en}</td>`;
                for (const v of item.values) {
                    const displayV = v === null ? '-' : v.toLocaleString('vi-VN');
                    t += `<td style="text-align: right; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">${displayV}</td>`;
                }
                t += `</tr>`;
            }
            t += `</tbody></table></div></div>`;
            return t;
        };

        // 3. Income Statement & Balance Sheet
        html += renderTableHTML('Kết quả kinh doanh (Rút gọn)', data.income_statement?.items, data.periods);
        html += renderTableHTML('Cân đối kế toán (Rút gọn)', data.balance_sheet?.items, data.periods);

        html += '</div>';
        tableBody.innerHTML = `<tr><td style="padding: 0;">${html}</td></tr>`;
    }

    '''

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_code + content[end_idx:]

app_path.write_text(content, encoding='utf-8')
