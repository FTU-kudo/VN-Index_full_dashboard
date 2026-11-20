    // =========================================================
    // FINANCIAL CHARTS SUB-TAB (BIỂU ĐỒ TÀI CHÍNH) - POWERED BY ECHARTS
    // =========================================================
    let chartInstances = [];

    function renderFinancialCharts() {
        // Clear previous charts to prevent memory leaks
        chartInstances.forEach(chart => chart.dispose());
        chartInstances = [];

        if (!currentTicker || !window.YUANTA_CHART_DATA || !window.YUANTA_CHART_DATA[currentTicker]) {
            tableHead.innerHTML = `<tr><th>Biểu đồ tài chính</th></tr>`;
            tableBody.innerHTML = `<tr><td style="text-align: center; padding: 2rem;">Chưa có dữ liệu biểu đồ cho mã ${currentTicker}. Đang đồng bộ hoặc không khả dụng.</td></tr>`;
            return;
        }

        const chartData = window.YUANTA_CHART_DATA[currentTicker];
        
        tableHead.innerHTML = `<tr><th>Tóm tắt Xu hướng Tài chính & Hiệu quả Kinh doanh (ECharts)</th></tr>`;
        
        // Define which charts to show in the grid
        const layoutKeys = [
            'net_revenue_2', 'net_profit_2', 'valuation_2', 
            'equity_1', 'structure_asset_1', 'profit_margin_2',
            'equity_used_ratio_1', 'accounting_balance_1', 'asset_1',
            'cash_flow_1', 'liquidity_ability_1'
        ];

        let html = `<tr><td style="padding: 1rem;"><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; background: var(--bg-main);">`;
        
        layoutKeys.forEach(key => {
            if (chartData[key]) {
                html += `
                    <div class="glass-panel" style="padding: 1rem; position: relative;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem; font-size: 0.95rem; display: flex; justify-content: space-between;">
                            ${chartData[key].title.chart_name || 'Biểu đồ'} 
                            <i class="fas fa-chart-line" style="color: var(--text-secondary);"></i>
                        </h4>
                        <div id="echart-${key}" style="width: 100%; height: 300px;"></div>
                    </div>
                `;
            }
        });
        
        html += `</div></td></tr>`;
        tableBody.innerHTML = html;

        // Initialize ECharts instances
        layoutKeys.forEach(key => {
            if (chartData[key]) {
                initEChart(`echart-${key}`, chartData[key]);
            }
        });
    }

    function initEChart(elementId, dataObj) {
        const dom = document.getElementById(elementId);
        if (!dom) return;
        const myChart = echarts.init(dom);
        chartInstances.push(myChart);

        const titleObj = dataObj.title || {};
        const unitObj = dataObj.unit || {};
        const rawData = dataObj.data || [];

        const times = rawData.map(d => d.time);
        
        const seriesData = [];
        const legendData = [];
        const yAxisIds = new Set(); // 0 for left, 1 for right

        // Scan for value_1 up to value_5
        for (let i = 1; i <= 5; i++) {
            const vKey = `value_${i}`;
            if (titleObj[vKey]) {
                const sName = titleObj[vKey];
                const sUnit = unitObj[vKey] || '';
                const sType = (sUnit === '%' || sUnit === 'Lần' || i > 1) ? 'line' : 'bar';
                const yIndex = (sUnit === '%' || sUnit === 'Lần' || sUnit === 'Ngày') ? 1 : 0;
                yAxisIds.add(yIndex);
                
                legendData.push(sName);
                seriesData.push({
                    name: sName,
                    type: sType,
                    yAxisIndex: yIndex,
                    smooth: true,
                    data: rawData.map(d => d[vKey] !== undefined ? d[vKey] : null),
                    tooltip: { valueFormatter: value => value ? `${value} ${sUnit}` : '-' }
                });
            }
        }

        const yAxes = [];
        if (yAxisIds.has(0)) {
            yAxes.push({ type: 'value', name: '', splitLine: { lineStyle: { color: '#333' } } });
        } else {
            yAxes.push({ type: 'value', show: false }); // Dummy left axis
        }
        
        if (yAxisIds.has(1)) {
            yAxes.push({ type: 'value', name: '', splitLine: { show: false } });
        } else {
            yAxes.push({ type: 'value', show: false });
        }

        const option = {
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, backgroundColor: 'rgba(20,20,20,0.9)', borderColor: '#444', textStyle: { color: '#fff' } },
            legend: { data: legendData, bottom: 0, textStyle: { color: '#aaa', fontSize: 11 } },
            grid: { left: '3%', right: '3%', bottom: '15%', top: '10%', containLabel: true },
            xAxis: [ { type: 'category', data: times, axisLabel: { color: '#888', fontSize: 10, rotate: 45 } } ],
            yAxis: yAxes,
            series: seriesData,
            color: ['#8b5cf6', '#f97316', '#10b981', '#3b82f6', '#ec4899']
        };

        myChart.setOption(option);
    }
