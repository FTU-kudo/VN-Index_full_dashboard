document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('ticker-search');
    const searchResults = document.getElementById('search-results');
    const emptyState = document.getElementById('empty-state');
    const dataView = document.getElementById('data-view');
    const themeToggle = document.querySelector('.theme-toggle');
    
    // BCTC elements
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');
    const periodBtns = document.querySelectorAll('.period-selection .period-btn');
    const chartPeriodBtns = document.querySelectorAll('#chart-period-toggles .period-btn');
    let activeChartPeriod = '2';
    const periodCountSelect = document.getElementById('period-count');
    const unitScaleSelect = document.getElementById('unit-scale');
    const yearSelect = document.getElementById('year-select');
    
    // Tabs
    const tabItems = document.querySelectorAll('.tab-item');
    const tabOverview = document.getElementById('tab-overview');
    const tabBctc = document.getElementById('tab-bctc');
    const tabNews = document.getElementById('tab-news');
    const tabPeers = document.getElementById('tab-peers');
    const tabTrading = document.getElementById('tab-trading');
    const tabPlaceholder = document.getElementById('tab-placeholder');
    const placeholderTitle = document.getElementById('placeholder-title');
    
    // Modal elements
    const ratingModal = document.getElementById('rating-modal');
    const btnRatingGuide = document.getElementById('btn-rating-guide');
    const closeRatingModal = document.getElementById('close-rating-modal');
    const modalTabs = document.querySelectorAll('.modal-tab');
    const guideSections = document.querySelectorAll('.guide-section');
    
    let currentTicker = 'ACB'; // Default landing stock (Yuanta Profile demo)
    
    // Gather available tickers from Master Universe (1,525 stocks), BCTC, and Profile datasets
    const universeStocks = window.STOCK_UNIVERSE || [];
    const bctcTickers = window.BCTC_DATA ? Object.keys(window.BCTC_DATA) : [];
    const profileTickers = window.YUANTA_PROFILE_DATA ? Object.keys(window.YUANTA_PROFILE_DATA) : [];
    const fallbackTickers = [...new Set([...bctcTickers, ...profileTickers])].sort();
    
    // Populate Year Select for BCTC
    const allPeriods = window.PERIODS || ["2025_Q4", "2025_Q3", "2025_Q2", "2025_Q1", "2024_Q4"];
    const uniqueYears = [...new Set(allPeriods.map(p => p.split('_')[0]))].sort().reverse();
    if (yearSelect) {
        uniqueYears.forEach(y => {
            const option = document.createElement('option');
            option.value = y;
            option.textContent = y;
            yearSelect.appendChild(option);
        });
    }
    
    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        themeToggle.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
    });
    
    // Search Autocomplete across 1,525 Stocks Universe (HOSE, HNX, UPCOM)
    searchInput.addEventListener('input', (e) => {
        const val = e.target.value.trim().toUpperCase();
        searchResults.innerHTML = '';
        
        if (!val) {
            searchResults.classList.add('hidden');
            return;
        }
        
        let matches = [];
        if (universeStocks.length > 0) {
            matches = universeStocks.filter(item => 
                item.symbol.includes(val) || 
                item.sector.toUpperCase().includes(val) || 
                item.exchange.toUpperCase() === val
            ).slice(0, 15);
        } else {
            matches = fallbackTickers.filter(t => t.includes(val)).slice(0, 12).map(sym => ({
                symbol: sym,
                exchange: "HOSE",
                sector: "Đang cập nhật"
            }));
        }
        
        if (matches.length > 0) {
            matches.forEach(item => {
                const div = document.createElement('div');
                div.className = 'search-result-item';
                div.style.display = 'flex';
                div.style.justifyContent = 'space-between';
                div.style.alignItems = 'center';
                div.style.padding = '8px 12px';
                div.style.borderBottom = '1px solid var(--border-color)';
                div.style.cursor = 'pointer';
                
                const hasProfile = window.YUANTA_PROFILE_DATA && window.YUANTA_PROFILE_DATA[item.symbol] ? ' ⭐' : '';
                const exColor = item.exchange === 'HOSE' ? '#3b82f6' : (item.exchange === 'HNX' ? '#10b981' : '#f59e0b');
                
                div.innerHTML = `
                    <div>
                        <strong style="font-size: 1.05rem; color: var(--text-primary);">${item.symbol}</strong>${hasProfile}
                        <span style="font-size: 0.82rem; color: var(--text-secondary); margin-left: 8px;">${item.sector}</span>
                    </div>
                    <span style="background: ${exColor}; color: white; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">${item.exchange}</span>
                `;
                div.addEventListener('click', () => selectTicker(item.symbol));
                div.addEventListener('mouseenter', () => div.style.backgroundColor = 'var(--bg-hover)');
                div.addEventListener('mouseleave', () => div.style.backgroundColor = 'transparent');
                searchResults.appendChild(div);
            });
            searchResults.classList.remove('hidden');
        } else {
            searchResults.classList.add('hidden');
        }
    });
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const val = searchInput.value.trim().toUpperCase();
            if (!val) return;
            
            let targetSymbol = val;
            if (universeStocks.length > 0) {
                const exact = universeStocks.find(item => item.symbol === val);
                if (exact) {
                    targetSymbol = exact.symbol;
                } else {
                    const firstMatch = universeStocks.find(item => item.symbol.startsWith(val) || item.symbol.includes(val));
                    if (firstMatch) targetSymbol = firstMatch.symbol;
                }
            } else if (fallbackTickers.length > 0) {
                const first = fallbackTickers.find(t => t.startsWith(val));
                if (first) targetSymbol = first;
            }
            selectTicker(targetSymbol);
            searchResults.classList.add('hidden');
            searchInput.blur();
        }
    });
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.classList.add('hidden');
        }
    });

    // Tab switching handler
    tabItems.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabItems.forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            const targetTab = e.currentTarget.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    function switchTab(tabName) {
        tabOverview.classList.add('hidden');
        tabBctc.classList.add('hidden');
        if (tabPeers) tabPeers.classList.add('hidden');
        if (tabTrading) tabTrading.classList.add('hidden');
        tabPlaceholder.classList.add('hidden');
        if (tabNews) tabNews.style.display = 'none';
        
        if (tabName === 'overview') {
            tabOverview.classList.remove('hidden');
            renderOverview(currentTicker);
        } else if (tabName === 'bctc') {
            tabBctc.classList.remove('hidden');
            renderActiveFinancialView();
        } else if (tabName === 'news') {
            if (tabNews) tabNews.style.display = 'block';
            renderEvents(currentTicker);
        } else if (tabName === 'peers') {
            if (tabPeers) tabPeers.classList.remove('hidden');
            renderOverview(currentTicker);
            const peerSec = document.getElementById('section-peers');
            if (peerSec) peerSec.scrollIntoView({ behavior: 'smooth' });
        } else if (tabName === 'trading') {
            if (tabTrading) tabTrading.classList.remove('hidden');
            renderTrading(currentTicker);
        } else {
            tabPlaceholder.classList.remove('hidden');
            if (tabName === 'news') placeholderTitle.textContent = 'Tin tức & Sự kiện Doanh nghiệp';
        }

        
        // Ensure all charts resize correctly when a tab becomes visible
        setTimeout(() => {
            chartInstances.forEach(chart => {
                if (chart) chart.resize();
            });
        }, 50);
    }
    
    // Modal Event Listeners
    if (btnRatingGuide && ratingModal) {
        btnRatingGuide.addEventListener('click', () => {
            ratingModal.classList.remove('hidden');
        });
        
        closeRatingModal.addEventListener('click', () => {
            ratingModal.classList.add('hidden');
        });
        
        ratingModal.addEventListener('click', (e) => {
            if (e.target === ratingModal) {
                ratingModal.classList.add('hidden');
            }
        });
    }

    // Modal Tabs logic
    modalTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs & sections
            modalTabs.forEach(t => t.classList.remove('active'));
            guideSections.forEach(s => s.classList.add('hidden'));
            guideSections.forEach(s => s.classList.remove('active'));
            
            // Add active to clicked
            tab.classList.add('active');
            const targetId = tab.getAttribute('data-target');
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.remove('hidden');
                targetSection.classList.add('active');
            }
        });
    });
    
    function selectTicker(ticker) {
        currentTicker = ticker;
        searchInput.value = ticker;
        searchResults.classList.add('hidden');
        
        emptyState.classList.add('hidden');
        dataView.classList.remove('hidden');
        
        // Render both views
        renderOverview(ticker);
        if (typeof renderActiveFinancialView === 'function') renderActiveFinancialView();
        if (typeof renderTrading === 'function') renderTrading(ticker);
    }
    
    // Number Formatting Helpers
    function formatInt(val) {
        if (val === null || val === undefined || isNaN(val)) return '0';
        return new Intl.NumberFormat('en-US').format(Math.round(val));
    }

    function formatDec(val, decimals = 2) {
        if (val === null || val === undefined || isNaN(val)) return '0.00';
        return parseFloat(val).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    }

    function decodeHtmlEntities(str) {
        if (!str) return 'Chưa có thông tin cập nhật cho mã cổ phiếu này.';
        const txt = document.createElement("textarea");
        txt.innerHTML = str;
        return txt.value;
    }

    // =========================================================
    // RENDER YUANTA OVERVIEW TAB & RATING RATIOS (6 APIs Engine)
    // =========================================================
    function renderOverview(ticker) {
        // Retrieve cached profile data or provide default template
        const allProfiles = window.YUANTA_PROFILE_DATA || {};
        const profile = allProfiles[ticker] || null;
        
        if (!profile) {
            // Initiate asynchronous live fetch if not found in local bundle
            fetchLiveYuantaProfile(ticker);
            return;
        }
        
        const rInfo = profile.rating_info || {};
        const pBoard = (profile.price_board && profile.price_board[0]) ? profile.price_board[0] : {};
        const rScores = (profile.rating_scores && profile.rating_scores[0]) ? profile.rating_scores[0] : {};
        const sHolder = profile.shareholder || {};
        const pInfo = profile.profile_info || {};
        const peers = profile.peers || {};

        // 1. TOP HEADER PANEL UPDATE
        document.getElementById('ticker-symbol').textContent = ticker;
        document.getElementById('ticker-exchange').textContent = rInfo.Exchange || pBoard.Exchange || 'HSX';
        const sectorStr = (rInfo.SectorName || pInfo.IndustryViName || 'Thị trường').replace(/\bL[12]\b/g, '').trim();
        document.getElementById('ticker-company-name').textContent = `${rInfo.CompanyName || pInfo.CompanyNameVi || ticker} | ${sectorStr}`;
        
        // Price and change coloring
        const currentP = pBoard.LastMP || rInfo.CurrentPrice || 0;
        const refP = pBoard.RefP || currentP;
        const diff = currentP - refP;
        const pct = refP > 0 ? (diff / refP) * 100 : 0;
        
        const priceEl = document.getElementById('ticker-current-price');
        const changeEl = document.getElementById('ticker-price-change');
        priceEl.textContent = formatInt(currentP);
        
        changeEl.className = 'price-change ';
        if (diff > 0) {
            changeEl.textContent = `+ ${formatInt(diff)} (+${formatDec(pct, 2)}%)`;
            changeEl.classList.add('price-up');
            priceEl.style.color = '#10b981';
        } else if (diff < 0) {
            changeEl.textContent = `${formatInt(diff)} (${formatDec(pct, 2)}%)`;
            changeEl.classList.add('price-down');
            priceEl.style.color = '#ef4444';
        } else {
            changeEl.textContent = `+ 0 (0%)`;
            changeEl.classList.add('price-ref');
            priceEl.style.color = '#f59e0b';
        }

        // Scores & Trading Stats
        const stockRating = rInfo.StockRatingPoint || rScores.StockRating || 0;
        const basicPoint = rInfo.BasicPoint || rScores.FundamentalPoint || 0;
        const priceStrength = rInfo.PriceStrength || rScores.TechnicalPoint || 0;
        
        const srEl = document.getElementById('val-stock-rating');
        const bpEl = document.getElementById('val-basic-point');
        const psEl = document.getElementById('val-price-strength');
        srEl.textContent = stockRating;
        bpEl.textContent = basicPoint;
        psEl.textContent = priceStrength;
        
        [srEl, bpEl, psEl].forEach((el, idx) => {
            const v = [stockRating, basicPoint, priceStrength][idx];
            el.className = 'score-val ' + (v >= 80 ? 'text-success' : (v >= 60 ? 'text-warning' : 'text-danger'));
        });

        const valGtgd = (pBoard.TotalVal || rInfo.Value || 0) / 1000000; // Trieu dong
        const valKlgd = (pBoard.TotalVol || rInfo.Volume || 0);
        document.getElementById('val-gtgd').innerHTML = `${formatInt(valGtgd)} <span style="font-size: 0.75rem; font-weight: 500; color: var(--text-secondary);">triệu đồng</span>`;
        document.getElementById('val-klgd').innerHTML = `${formatInt(valKlgd)} <span style="font-size: 0.75rem; font-weight: 500; color: var(--text-secondary);">CP</span>`;

        // Recommendation Box (Aligned with Yuanta Official Website & API Codes)
        const recommDate = rInfo.RecommendationDate ? rInfo.RecommendationDate.split('-').reverse().join('/') : 'N/A';
        
        // ShortTermTrend: 1 = Tăng, 2 = Giảm, 3 / -1 = Đi ngang
        const trendEl = document.getElementById('val-trend');
        if (rInfo.ShortTermTrend === 1) { 
            trendEl.textContent = '↗ Tăng'; 
            trendEl.style.color = '#10b981'; 
        } else if (rInfo.ShortTermTrend === 2 || rInfo.ShortTermTrend === -1) { 
            trendEl.textContent = '↘ Giảm'; 
            trendEl.style.color = '#ef4444'; 
        } else { 
            trendEl.textContent = '→ Đi ngang'; 
            trendEl.style.color = '#f59e0b'; 
        }

        // Recommend: 1 or 2 = Mua, 3 = Nắm giữ, 4 = Quan sát, 5 = Bán
        const recEl = document.getElementById('val-recommend');
        const recVal = rInfo.Recommend;
        let isWatching = false;
        if (recVal === 4) { 
            recEl.textContent = 'Quan sát'; 
            recEl.style.color = '#3b82f6'; // Blue text matching Yuanta Web
            isWatching = true;
        } else if (recVal === 3) { 
            recEl.textContent = 'Nắm giữ'; 
            recEl.style.color = '#f59e0b'; 
        } else if (recVal === 1 || recVal === 2) { 
            recEl.textContent = 'Mua'; 
            recEl.style.color = '#10b981'; 
        } else { 
            recEl.textContent = 'Bán'; 
            recEl.style.color = '#ef4444'; 
        }

        const dateEl = document.getElementById('val-recomm-date');
        if (isWatching || !rInfo.BuyPrice) {
            dateEl.textContent = recommDate;
        } else {
            dateEl.textContent = `${recommDate} (T+${rInfo.TradingT || 0})`;
        }

        const optW = rInfo.OptimumWeight !== undefined && rInfo.OptimumWeight !== null ? (rInfo.OptimumWeight <= 1 ? rInfo.OptimumWeight * 100 : rInfo.OptimumWeight) : 0;
        document.getElementById('val-opt-weight').textContent = `${formatDec(optW, 2)}%`;
        
        if (isWatching || !rInfo.BuyPrice || rInfo.BuyPrice <= 0) {
            document.getElementById('val-buy-price').textContent = '-- (--)';
            document.getElementById('val-target-price').textContent = '--';
            document.getElementById('val-stop-loss').textContent = '--';
        } else {
            const bp = rInfo.BuyPrice;
            const diffPct = bp > 0 ? ((currentP - bp) / bp) * 100 : 0;
            const sign = diffPct >= 0 ? '+' : '';
            document.getElementById('val-buy-price').innerHTML = `${formatInt(bp)} <span style="font-size: 0.8rem; color: ${diffPct >= 0 ? '#10b981' : '#ef4444'};">(${sign}${formatDec(diffPct, 2)}%)</span>`;
            document.getElementById('val-target-price').textContent = rInfo.TargetPrice ? formatInt(rInfo.TargetPrice) : '--';
            document.getElementById('val-stop-loss').textContent = rInfo.TrailingStop ? formatInt(rInfo.TrailingStop) : '--';
        }

        // 2. CARD 1: COMPANY OVERVIEW & 12 FINANCIAL KPIs
        document.getElementById('card-about-title').textContent = `📌 Về ${ticker}`;
        document.getElementById('profile-overview-text').innerHTML = decodeHtmlEntities(pInfo.Overview);

        const kpiItems = [
            { label: 'Vốn hóa', value: `${formatDec((rInfo.MarketCap || 0)/1000, 1)} tỷ` },
            { label: 'KLGD TB 20 phiên', value: `${formatInt(rInfo.AVGVolume20 || 0)}` },
            { label: 'KLCP lưu hành', value: `${formatInt(rInfo.TotalMarketShares || pInfo.ListedShares || 0)} CP` },
            { label: 'Tỷ lệ freefloat', value: `${formatDec(rInfo.FreeFloatRate || 0, 1)}%` },
            { label: 'P/B', value: `${formatDec(rInfo.PB || 0, 2)}` },
            { label: 'P/S', value: `${formatDec(rInfo.PS || 0, 2)}` },
            { label: 'ROA', value: `${formatDec(rInfo.ROA || 0, 2)}%` },
            { label: 'ROE (TTM)', value: `${formatDec(rInfo.ROE || 0, 2)}%` },
            { label: 'EPS (TTM)', value: `${formatInt(rInfo.EPS || 0)} VNĐ` },
            { label: 'P/E (TTM)', value: `${formatDec(rInfo.PE || 0, 2)}x` },
            { label: 'Tỷ suất cổ tức', value: `${formatDec(rInfo.DividendRate || 0, 2)}%` },
            { label: 'EV/EBITDA (TTM)', value: `${formatDec(rInfo.EV_EVBIT || 0, 2)}` }
        ];

        const kpisContainer = document.getElementById('profile-kpis');
        kpisContainer.innerHTML = kpiItems.map(item => `
            <div class="kpi-box">
                <div class="kpi-label">${item.label}</div>
                <div class="kpi-value">${item.value}</div>
            </div>
        `).join('');

        // 3. CARD 2: GENERAL INFO & DONUT SHAREHOLDER CHART
        document.getElementById('info-comp-name').textContent = pInfo.CompanyNameVi || rInfo.CompanyName || ticker;
        
        let estD = pInfo.EstablishedDate || '-';
        if (estD.includes('-')) estD = estD.split('-').reverse().join('/');
        document.getElementById('info-est-date').textContent = estD;
        
        let industryName = pInfo.IndustryViName || rInfo.SectorName || 'Tài chính - Ngân hàng';
        document.getElementById('info-industry').textContent = industryName.replace(/\bL[12]\b/g, '').trim();
        document.getElementById('info-rep-name').textContent = pInfo.ContactPerson || 'Ông Từ Tiến Phát';
        document.getElementById('info-rep-pos').textContent = pInfo.ContactPersonPosition || 'Tổng Giám đốc';
        document.getElementById('info-shares-count').textContent = `${formatInt(pInfo.ListedShares || rInfo.TotalMarketShares)} cổ phiếu`;

        // Render Donut Chart via pure modern CSS Conic Gradient
        const foreign = sHolder.ForeignPercentage || 28.53;
        const state = sHolder.StatePercentage || 0;
        const other = sHolder.OtherPercentage || (100 - foreign - state);
        
        const p1 = foreign;
        const p2 = foreign + state;
        const gradient = `conic-gradient(#8b5cf6 0% ${p1}%, #f97316 ${p1}% ${p2}%, #64748b ${p2}% 100%)`;

        const shSection = document.getElementById('shareholder-section');
        shSection.innerHTML = `
            <div class="donut-chart-container" style="background: ${gradient};">
                <div class="donut-center"><strong style="color: var(--text-primary); font-size: 1rem;">${ticker}</strong></div>
            </div>
            <div class="legend-list">
                <div class="legend-item"><span class="legend-color color-foreign"></span> Nước ngoài (${formatDec(foreign, 2)}%)</div>
                <div class="legend-item"><span class="legend-color color-state"></span> Nhà nước (${formatDec(state, 2)}%)</div>
                <div class="legend-item"><span class="legend-color color-other"></span> Khác (${formatDec(other, 2)}%)</div>
            </div>
        `;

        // 4. CARD 3: PEERS TABLE (Danh sách các mã cùng ngành)
        document.getElementById('val-industry-pe').textContent = formatDec(peers.AveragePE || 8.51, 2);
        
        const peerList = peers.Peer || [];
        const peersTbody = document.getElementById('peers-tbody');
        
        if (peerList.length === 0) {
            peersTbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted);">Không tìm thấy dữ liệu đối thủ cạnh tranh cho mã này.</td></tr>`;
        } else {
            peersTbody.innerHTML = peerList.map(item => {
                const pChange = item.Change || 0;
                const pColor = pChange > 0 ? '#10b981' : (pChange < 0 ? '#ef4444' : '#f59e0b');
                const pSign = pChange > 0 ? '+' : '';
                const rClass = item.StockRating >= 80 ? 'rating-high' : (item.StockRating >= 60 ? 'rating-mid' : 'rating-low');
                
                return `
                    <tr onclick="window.selectTickerFromPeer('${item.StockCode}')">
                        <td><strong style="color: var(--primary); font-size: 0.95rem;">${item.StockCode}</strong></td>
                        <td style="font-weight: 700; color: ${pColor};">${formatInt(item.Price)}</td>
                        <td style="font-weight: 600; color: ${pColor};">${pSign}${formatInt(pChange)} (${pSign}${formatDec(item.PerChange, 2)}%)</td>
                        <td><span class="rating-badge ${rClass}">${item.StockRating || '-'}</span></td>
                        <td>${formatDec(item.PE, 2)}</td>
                        <td>${formatDec(item.PB, 2)}</td>
                        <td>${formatInt(item.EPS)}</td>
                        <td>${formatDec(item.ROA, 2)}%</td>
                        <td>${formatDec(item.ROE, 2)}%</td>
                        <td>${formatDec(item.Beta, 2)}</td>
                    </tr>
                `;
            }).join('');
        }
        
        renderCorrelateChart(ticker);
    }
    
    function getChartThemeColors() {
        return {
            stock: '#ff4d4f', // Red-orange for stock
            sector: '#1890ff', // Blue for sector
            text: document.body.classList.contains('dark-mode') ? '#ccc' : '#666',
            splitLine: document.body.classList.contains('dark-mode') ? '#333' : '#e5e7eb'
        };
    }

    function renderBarChartVertical(containerId, apiData, ticker) {
        const container = document.getElementById(containerId);
        if (!container) return;
        if (!apiData || !apiData.Data || apiData.Data.length === 0) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu</div>';
            return;
        }
        
        if (container.innerHTML.includes('Không có dữ liệu')) {
            container.innerHTML = '';
        }
        
        let chartData = apiData.Data;

        // Nếu cổ phiếu không có bất kỳ dữ liệu nào (> 0) trong mục này (VD: Ngân hàng không có Khả năng hoạt động)
        const hasStockData = chartData.some(item => Math.abs(item.Value1) > 0.0001);
        if (!hasStockData) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu để so sánh</div>';
            return;
        }

        // Lọc bỏ các chỉ tiêu mà cả doanh nghiệp và ngành đều bằng 0
        chartData = chartData.filter(item => Math.abs(item.Value1) > 0.0001 || Math.abs(item.Value2) > 0.0001);
        
        if (chartData.length === 0) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu để so sánh</div>';
            return;
        }
        
        const sectorName = (apiData.Title && apiData.Title.Value2) ? apiData.Title.Value2 : 'Ngành';
        
        const theme = getChartThemeColors();
        const N = chartData.length;
        
        const grids = [];
        const xAxes = [];
        const yAxes = [];
        const series = [];
        
        chartData.forEach((item, index) => {
            const blockWidth = 100 / N;
            const left = (index * blockWidth + 2) + '%';
            const width = (blockWidth - 4) + '%';
            
            grids.push({
                left: left,
                width: width,
                bottom: '15%',
                top: '12%',
                containLabel: true
            });
            
            xAxes.push({
                gridIndex: index,
                type: 'category',
                data: [item.Name],
                axisLabel: { color: theme.text, interval: 0, width: 85, overflow: 'truncate' }
            });
            
            yAxes.push({
                gridIndex: index,
                type: 'value',
                splitLine: { lineStyle: { color: theme.splitLine, type: 'dashed' } },
                axisLabel: { 
                    color: theme.text,
                    formatter: function(val) { 
                        if (Math.abs(val) >= 1000000) return (val/1000000).toFixed(1) + 'M';
                        if (Math.abs(val) >= 1000) return (val/1000).toFixed(1) + 'k';
                        return val; 
                    }
                }
            });
            
            series.push({
                name: ticker,
                type: 'bar',
                xAxisIndex: index,
                yAxisIndex: index,
                data: [item.Value1],
                itemStyle: { color: theme.stock }
            });
            
            series.push({
                name: sectorName,
                type: 'bar',
                xAxisIndex: index,
                yAxisIndex: index,
                data: [item.Value2],
                itemStyle: { color: theme.sector }
            });
        });

        const option = {
            tooltip: { 
                trigger: 'axis', 
                axisPointer: { type: 'shadow' },
                formatter: function(params) {
                    let tooltipHtml = params[0].axisValueLabel + '<br/>';
                    const isPercent = params[0].axisValueLabel.includes('(%)');
                    params.forEach(p => {
                        let val = p.value !== undefined ? p.value : p.data;
                        let valStr = val;
                        if (isPercent) valStr += '%';
                        tooltipHtml += p.marker + ' ' + p.seriesName + ': <b>' + valStr + '</b><br/>';
                    });
                    return tooltipHtml;
                }
            },
            legend: { data: [ticker, sectorName], bottom: 0, textStyle: { color: theme.text } },
            grid: grids,
            xAxis: xAxes,
            yAxis: yAxes,
            series: series
        };
        
        let chart = echarts.getInstanceByDom(container);
        if (!chart) { chart = echarts.init(container); chartInstances.push(chart); }
        chart.setOption(option);
    }

    function renderBarChartHorizontal(containerId, apiData, ticker) {
        const container = document.getElementById(containerId);
        if (!container) return;
        if (!apiData || !apiData.Data || apiData.Data.length === 0) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu</div>';
            return;
        }
        
        if (container.innerHTML.includes('Không có dữ liệu')) {
            container.innerHTML = '';
        }
        
        let chartData = apiData.Data;

        // Nếu cổ phiếu không có bất kỳ dữ liệu nào (> 0) trong mục này
        const hasStockData = chartData.some(item => Math.abs(item.Value1) > 0.0001);
        if (!hasStockData) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu để so sánh</div>';
            return;
        }

        // Lọc bỏ các chỉ tiêu mà cả doanh nghiệp và ngành đều bằng 0
        chartData = chartData.filter(item => Math.abs(item.Value1) > 0.0001 || Math.abs(item.Value2) > 0.0001);

        if (chartData.length === 0) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu để so sánh</div>';
            return;
        }
        
        const sectorName = (apiData.Title && apiData.Title.Value2) ? apiData.Title.Value2 : 'Ngành';
        
        const theme = getChartThemeColors();
        const names = chartData.map(item => item.Name).reverse();
        const values1 = chartData.map(item => item.Value1).reverse();
        const values2 = chartData.map(item => item.Value2).reverse();
        
        const option = {
            tooltip: { 
                trigger: 'axis', 
                axisPointer: { type: 'shadow' },
                formatter: function(params) {
                    let tooltipHtml = params[0].axisValueLabel + '<br/>';
                    const isPercent = params[0].axisValueLabel.includes('(%)');
                    params.forEach(p => {
                        let val = p.value !== undefined ? p.value : p.data;
                        let valStr = val;
                        if (isPercent) valStr += '%';
                        tooltipHtml += p.marker + ' ' + p.seriesName + ': <b>' + valStr + '</b><br/>';
                    });
                    return tooltipHtml;
                }
            },
            legend: { data: [ticker, sectorName], bottom: 0, textStyle: { color: theme.text } },
            grid: { left: '3%', right: '4%', bottom: '15%', top: '5%', containLabel: true },
            xAxis: { 
                type: 'value', 
                splitLine: { lineStyle: { color: theme.splitLine, type: 'dashed' } }, 
                axisLabel: { 
                    color: theme.text,
                    formatter: function(val) {
                        if (Math.abs(val) >= 1000000) return (val/1000000).toFixed(1) + 'M';
                        if (Math.abs(val) >= 1000) return (val/1000).toFixed(1) + 'k';
                        return val;
                    }
                } 
            },
            yAxis: { type: 'category', data: names, axisLabel: { color: theme.text, width: 100, overflow: 'truncate' } },
            series: [
                { name: ticker, type: 'bar', data: values1, itemStyle: { color: theme.stock } },
                { name: sectorName, type: 'bar', data: values2, itemStyle: { color: theme.sector } }
            ]
        };
        
        let chart = echarts.getInstanceByDom(container);
        if (!chart) { chart = echarts.init(container); chartInstances.push(chart); }
        chart.setOption(option);
    }

    function renderRadarChart(containerId, apiData, ticker) {
        const container = document.getElementById(containerId);
        if (!container) return;
        if (!apiData || !apiData.Data || apiData.Data.length === 0) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu</div>';
            return;
        }
        
        if (container.innerHTML.includes('Không có dữ liệu')) {
            container.innerHTML = '';
        }
        
        let chartData = apiData.Data;

        // Đối với biểu đồ Radar (Khả năng sinh lợi), KHÔNG lọc dữ liệu = 0 
        // để luôn duy trì đủ các yếu tố (thường là 6) của ngành tạo thành hình đa giác trực quan.
        
        // Kiểm tra xem cổ phiếu có dữ liệu để so sánh không
        const hasStockData = chartData.some(item => Math.abs(item.Value1) > 0.0001);
        if (!hasStockData) {
            let chart = echarts.getInstanceByDom(container);
            if (chart) echarts.dispose(chart);
            container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:#888;">Không có dữ liệu để so sánh</div>';
            return;
        }

        const sectorName = (apiData.Title && apiData.Title.Value2) ? apiData.Title.Value2 : 'Ngành';
        
        const theme = getChartThemeColors();
        const indicator = chartData.map(item => ({ name: item.Name, max: Math.max(item.Value1, item.Value2) * 1.2 || 100 }));
        const values1 = chartData.map(item => item.Value1);
        const values2 = chartData.map(item => item.Value2);
        
        const option = {
            tooltip: { trigger: 'item' },
            legend: { data: [ticker, sectorName], bottom: 0, textStyle: { color: theme.text } },
            radar: {
                indicator: indicator,
                splitNumber: 5,
                shape: 'polygon',
                axisName: { color: theme.text },
                splitLine: { lineStyle: { color: [theme.splitLine] } },
                splitArea: { show: false },
                axisLine: { lineStyle: { color: theme.splitLine } },
                center: ['50%', '45%'], // Đẩy biểu đồ lên trên một chút
                radius: '60%' // Thu nhỏ radar lại để không đè vào legend
            },
            series: [{
                type: 'radar',
                data: [
                    { value: values1, name: ticker, itemStyle: { color: theme.stock }, areaStyle: { color: theme.stock, opacity: 0.3 } },
                    { value: values2, name: sectorName, itemStyle: { color: theme.sector }, areaStyle: { color: theme.sector, opacity: 0.3 } }
                ]
            }]
        };
        
        let chart = echarts.getInstanceByDom(container);
        if (!chart) { chart = echarts.init(container); chartInstances.push(chart); }
        chart.setOption(option);
    }

    function getLatestCSTCValue(ticker, fieldName) {
        const cstcData = window.YUANTA_CSTC_DATA && window.YUANTA_CSTC_DATA[ticker];
        if (!cstcData || !cstcData.detail) return 0;
        
        for (const group of cstcData.detail) {
            if (!group.data) continue;
            const fieldObj = group.data.find(item => item.field_name && item.field_name.toLowerCase().includes(fieldName.toLowerCase()));
            if (fieldObj && fieldObj.value && Array.isArray(fieldObj.value)) {
                for (let v of fieldObj.value) {
                    if (v !== null && v !== undefined && v !== "") return parseFloat(v) || 0;
                }
            }
        }
        return 0;
    }

    function getIndustryMedianCSTCValue(fieldName, industrySector) {
        if (!window.YUANTA_PROFILE_DATA || !window.YUANTA_CSTC_DATA) return 0;
        
        let values = [];
        for (const [tck, pData] of Object.entries(window.YUANTA_PROFILE_DATA)) {
            const sector = (pData.rating_info && pData.rating_info.SectorName) ? pData.rating_info.SectorName : '';
            if (sector.toLowerCase().includes(industrySector.toLowerCase())) {
                const val = getLatestCSTCValue(tck, fieldName);
                if (val !== null && val !== 0 && !isNaN(val)) {
                    values.push(val);
                }
            }
        }
        
        if (values.length === 0) return 0;
        values.sort((a, b) => a - b);
        const mid = Math.floor(values.length / 2);
        if (values.length % 2 === 0) {
            return (values[mid - 1] + values[mid]) / 2;
        } else {
            return values[mid];
        }
    }

    function renderBankCorrelateChart(ticker, sector) {
        const grid = document.querySelector('.correlate-grid');
        if (!grid) return;
        
        grid.innerHTML = `
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Khả năng sinh lợi</h4>
                <div id="bank-chart-profitability" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Khả năng thanh khoản</h4>
                <div id="bank-chart-liquidity" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Chất lượng tài sản</h4>
                <div id="bank-chart-asset-quality" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Định giá</h4>
                <div id="bank-chart-valuation" class="echarts-container"></div>
            </div>
        `;
        
        const metricsProfit = [
            { label: 'YOEA (%)', field: 'Tỷ suất sinh lợi của Tài sản Có sinh lãi' },
            { label: 'COF (%)', field: 'chi phí hình thành Tài sản Có sinh lãi' },
            { label: 'NIM (%)', field: 'thu nhập lãi thuần (NIM)' },
            { label: 'CIR (%)', field: 'chi phí hoạt động/Tổng thu nhập' },
            { label: 'Tăng trưởng TN (%)', field: 'Tăng trưởng tổng thu nhập HĐKD' },
            { label: 'ROE (%)', field: 'ROE' }
        ];
        
        const metricsLiquidity = [
            { label: 'LDR (%)', field: 'Dư nợ cho vay khách hàng/Tổng vốn huy động' },
            { label: 'Cho vay/Tổng TS (%)', field: 'Dư nợ cho vay/Tổng tài sản' },
            { label: 'VCSH/Tổng TS (%)', field: 'Vốn chủ sở hữu/Tổng tài sản Có' }
        ];
        
        const metricsAssetQuality = [
            { label: 'Dự phòng rủi ro/Dư nợ (%)', field: 'Dự phòng rủi ro tín dụng/Tổng dư nợ' },
            { label: 'TS sinh lãi/Tổng TS (%)', field: 'Tài sản Có sinh lãi/Tổng tài sản Có' }
        ];
        
        const metricsValuation = [
            { label: 'P/E', field: 'P/E' },
            { label: 'P/B', field: 'P/B' }
        ];
        
        function buildChartData(metrics) {
            return metrics.map(m => {
                let val1 = getLatestCSTCValue(ticker, m.field) || 0;
                let val2 = getIndustryMedianCSTCValue(m.field, 'Ngân hàng') || 0;
                return { 
                    Name: m.label, 
                    Value1: Math.round(val1 * 100) / 100, 
                    Value2: Math.round(val2 * 100) / 100 
                };
            });
        }
        
        setTimeout(() => {
            renderRadarChart('bank-chart-profitability', { Data: buildChartData(metricsProfit), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartHorizontal('bank-chart-liquidity', { Data: buildChartData(metricsLiquidity), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartVertical('bank-chart-asset-quality', { Data: buildChartData(metricsAssetQuality), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartVertical('bank-chart-valuation', { Data: buildChartData(metricsValuation), Title: { Value2: 'Trung vị ngành' } }, ticker);
        }, 50);
    }

    function renderCorporateChart(ticker, sector) {
        const grid = document.querySelector('.correlate-grid');
        if (!grid) return;
        
        grid.innerHTML = `
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Khả năng sinh lợi & Hiệu quả</h4>
                <div id="corporate-chart-profitability" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Đòn bẩy tài chính & Cơ cấu vốn</h4>
                <div id="corporate-chart-leverage" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Tốc độ Tăng trưởng</h4>
                <div id="corporate-chart-growth" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 1;">
                <h4>Dòng tiền & Thanh khoản</h4>
                <div id="corporate-chart-cashflow" class="echarts-container"></div>
            </div>
            <div class="correlate-card" style="grid-column: span 2;">
                <h4>Định giá</h4>
                <div id="corporate-chart-valuation" class="echarts-container"></div>
            </div>
        `;
        
        const metricsProfit = [
            { label: 'ROE (%)', field: 'ROE bình quân 4 quý gần nhất' },
            { label: 'ROA (%)', field: 'ROA bình quân 4 quý gần nhất' },
            { label: 'Biên lãi gộp (%)', field: 'Tỷ suất lợi nhuận gộp biên' },
            { label: 'Biên lãi thuần (%)', field: 'Tỷ suất sinh lợi trên doanh thu thuần' },
            { label: 'Vòng quay TTS', field: 'Vòng quay tổng tài sản' },
            { label: 'Nợ vay/VCSH (%)', field: 'Nợ vay trên Vốn chủ sở hữu' }
        ];
        
        const metricsLeverage = [
            { label: 'Nợ vay/Tổng TS (%)', field: 'Nợ vay trên Tổng tài sản' },
            { label: 'Nợ vay/VCSH (%)', field: 'Nợ vay trên Vốn chủ sở hữu' },
            { label: 'Nợ NH/Tổng nợ (%)', field: 'Nợ ngắn hạn trên Tổng nợ phải trả' }
        ];
        
        const metricsGrowth = [
            { label: 'Doanh thu thuần (%)', field: 'Tăng trưởng doanh thu thuần' },
            { label: 'Lợi nhuận trước thuế (%)', field: 'Tăng trưởng lợi nhuận trước thuế' },
            { label: 'Vốn chủ sở hữu (%)', field: 'Tăng trưởng vốn chủ sở hữu' },
            { label: 'Tổng tài sản (%)', field: 'Tăng trưởng tổng tài sản' }
        ];
        
        const metricsCashFlow = [
            { label: 'Thanh toán hiện hành', field: 'Tỷ số thanh toán hiện hành' },
            { label: 'Dòng tiền HĐKD/DTT (%)', field: 'dòng tiền HĐKD trên doanh thu thuần' },
            { label: 'Dòng tiền HĐKD/TTS (%)', field: 'Dòng tiền từ HĐKD trên Tổng tài sản' }
        ];
        
        const metricsValuation = [
            { label: 'P/E', field: 'P/E' },
            { label: 'P/B', field: 'P/B' },
            { label: 'P/S', field: 'P/S' }
        ];
        
        function buildChartData(metrics) {
            return metrics.map(m => {
                let val1 = getLatestCSTCValue(ticker, m.field) || 0;
                let val2 = getIndustryMedianCSTCValue(m.field, sector) || 0;
                return { 
                    Name: m.label, 
                    Value1: Math.round(val1 * 100) / 100, 
                    Value2: Math.round(val2 * 100) / 100 
                };
            });
        }
        
        setTimeout(() => {
            renderRadarChart('corporate-chart-profitability', { Data: buildChartData(metricsProfit), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartVertical('corporate-chart-leverage', { Data: buildChartData(metricsLeverage), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartHorizontal('corporate-chart-growth', { Data: buildChartData(metricsGrowth), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartVertical('corporate-chart-cashflow', { Data: buildChartData(metricsCashFlow), Title: { Value2: 'Trung vị ngành' } }, ticker);
            renderBarChartVertical('corporate-chart-valuation', { Data: buildChartData(metricsValuation), Title: { Value2: 'Trung vị ngành' } }, ticker);
        }, 50);
    }

    function renderCorrelateChart(ticker) {
        const pInfo = window.YUANTA_PROFILE_DATA && window.YUANTA_PROFILE_DATA[ticker];
        const sector = (pInfo && pInfo.rating_info && pInfo.rating_info.SectorName) ? pInfo.rating_info.SectorName : '';
        const lowerSector = sector.toLowerCase();
        
        if (lowerSector.includes('ngân hàng')) {
            renderBankCorrelateChart(ticker, sector);
        } else {
            renderCorporateChart(ticker, sector);
        }
    }

    // Make selectTicker callable from window for peer row clicks
    window.selectTickerFromPeer = function(ticker) {
        selectTicker(ticker);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Fallback: Attempt Live Fetching if online & CORS available
    async function fetchLiveYuantaProfile(ticker) {
        console.log(`Attempting live fetch for ${ticker} from Yuanta APIs...`);
        try {
            const resp = await fetch(`https://ysradarapi.yuanta.com.vn/api/v3/stock_rating/info/${ticker}?lang=vi`);
            if (resp.ok) {
                const json = await resp.json();
                if (json.success && json.response) {
                    // Update cache dynamically
                    window.YUANTA_PROFILE_DATA = window.YUANTA_PROFILE_DATA || {};
                    window.YUANTA_PROFILE_DATA[ticker] = { rating_info: json.response, price_board: [], rating_scores: [], shareholder: {}, profile_info: {}, peers: {} };
                    renderOverview(ticker);
                }
            }
        } catch (err) {
            console.warn(`Live Yuanta fetch blocked by CORS or network for ${ticker}. Using clean placeholder instead of cloning data.`);
            // Avoid cloning incorrect data from other stocks. Display transparent fallback.
            const universeMeta = (window.STOCK_UNIVERSE || []).find(x => x.symbol === ticker) || { symbol: ticker, exchange: "HOSE", sector: "Đang cập nhật" };
            const fallbackProfile = {
                rating_info: {
                    StockCode: ticker,
                    Exchange: universeMeta.exchange,
                    CompanyName: `Mã chứng khoán ${ticker}`,
                    SectorName: universeMeta.sector,
                    CurrentPrice: 0,
                    StockRatingPoint: 0,
                    BasicPoint: 0,
                    PriceStrength: 0,
                    Recommend: 4, // Quan sát
                    ShortTermTrend: 3, // Đi ngang
                    OptimumWeight: 0,
                    RecommendationDate: "N/A",
                    TradingT: 0,
                    Volume: 0,
                    Value: 0
                },
                price_board: [],
                rating_scores: [],
                shareholder: { ForeignPercentage: 0, StatePercentage: 0, OtherPercentage: 100 },
                profile_info: { Overview: `<p>Dữ liệu chi tiết của mã <b>${ticker}</b> hiện chưa được đồng bộ vào file cache tĩnh ngoại tuyến (<code>profile_data.js</code>). Do chính sách bảo mật CORS của trình duyệt, ứng dụng không thể gọi trực tiếp API Yuanta khi mở qua file cục bộ.</p><p>👉 <b>Cách khắc phục:</b> Hãy chạy lệnh <code>python dashboard/fetch_profile_data.py</code> (sau khi đã cập nhật danh mục mã cần theo dõi) hoặc cỗ máy đồng bộ 1,500 mã trên Terminal để tải dữ liệu thật 100% cho mã này về ổ cứng!</p>` },
                peers: {}
            };
            window.YUANTA_PROFILE_DATA = window.YUANTA_PROFILE_DATA || {};
            window.YUANTA_PROFILE_DATA[ticker] = fallbackProfile;
            renderOverview(ticker);
        }
    }

    // =========================================================
    // FINANCIAL TABS ENGINE (CSTC, BCTC, BIỂU ĐỒ)
    // =========================================================
    let activeSubTab = 'cstc'; // Default matching Yuanta Research UI
    const subTabBtns = document.querySelectorAll('.sub-tab-btn');
    
    subTabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            subTabBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.color = 'var(--text-primary)';
                b.style.border = '1px solid var(--border-color)';
                b.style.fontWeight = '500';
            });
            e.currentTarget.classList.add('active');
            e.currentTarget.style.background = '#8b5cf6';
            e.currentTarget.style.color = 'white';
            e.currentTarget.style.border = 'none';
            e.currentTarget.style.fontWeight = '600';
            
            activeSubTab = e.currentTarget.getAttribute('data-subtab') || 'cstc';
            renderActiveFinancialView();
        });
    });

    if (periodCountSelect && unitScaleSelect && yearSelect) {
        periodCountSelect.addEventListener('change', renderActiveFinancialView);
        unitScaleSelect.addEventListener('change', renderActiveFinancialView);
        yearSelect.addEventListener('change', renderActiveFinancialView);
        
        periodBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                periodBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                renderActiveFinancialView();
            });
        });
    }

    if (chartPeriodBtns) {
        chartPeriodBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                chartPeriodBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                activeChartPeriod = e.target.getAttribute('data-val');
                if (activeSubTab === 'chart') {
                    renderFinancialCharts();
                }
            });
        });
    }

    function renderActiveFinancialView() {
        const bctcControls = document.querySelector('.bctc-controls');
        const chartControls = document.querySelector('.chart-controls');
        const unitControl = document.getElementById('unit-scale').closest('.control-group');
        const reportControl = document.getElementById('report-type').closest('.control-group');
        
        if (activeSubTab === 'chart') {
            if (bctcControls) bctcControls.style.display = 'none';
            if (chartControls) chartControls.style.display = 'flex';
        } else {
            if (bctcControls) bctcControls.style.display = 'flex';
            if (chartControls) chartControls.style.display = 'none';
        }

        if (activeSubTab === 'cstc') {
            if (unitControl) unitControl.style.display = 'none';
            if (reportControl) reportControl.style.display = 'none';
        } else if (activeSubTab !== 'chart') {
            if (unitControl) unitControl.style.display = 'flex';
            if (reportControl) reportControl.style.display = 'flex';
        }

        if (activeSubTab === 'cstc') {
            renderCSTCTable();
        } else if (activeSubTab === 'chart') {
            renderFinancialCharts();
        } else {
            renderTable();
        }
    }

    // =========================================================
    // YUANTA FINANCIAL RATIOS (CHỈ SỐ TÀI CHÍNH - CSTC) RENDERER
    // =========================================================
    function renderCSTCTable() {
        const cstcData = (window.YUANTA_CSTC_DATA && window.YUANTA_CSTC_DATA[currentTicker]) ? window.YUANTA_CSTC_DATA[currentTicker] : null;
        
        if (!cstcData) {
            fetchLiveCSTC(currentTicker);
            return;
        }

        const titleData = (cstcData.title && cstcData.title.data) ? cstcData.title.data : [];
        const detailData = cstcData.detail || [];

        if (titleData.length === 0 || detailData.length === 0) {
            tableHead.innerHTML = `<tr><th>Chỉ tiêu tài chính</th></tr>`;
            tableBody.innerHTML = `<tr><td style="text-align: center; padding: 2rem;">Chưa có chỉ số tài chính hợp lệ cho mã ${currentTicker}.</td></tr>`;
            return;
        }

        // Identify the start index based on selected period on the UI
        let startIndex = -1;
        const selectedPeriodBtn = document.querySelector('.period-btn.active');
        const selectedTerm = selectedPeriodBtn ? selectedPeriodBtn.textContent.trim() : 'Q2';
        const selectedYear = yearSelect ? yearSelect.value : '2026';
        
        for (let i = 0; i < titleData.length; i++) {
            if (titleData[i].term_code === selectedTerm && titleData[i].year_period.toString() === selectedYear) {
                startIndex = i;
                break;
            }
        }

        // Every stock publishes at a different time.  For example, VIC may only have
        // Q1/2026 while the global control defaults to Q2/2026.  A missing exact period
        // must not discard the ticker's offline cache and attempt a browser-side API call.
        if (startIndex === -1) {
            const requestedPeriodOrder = getCSTCPeriodOrder(selectedTerm, selectedYear);
            const closestAvailableIndex = titleData.findIndex(period => {
                const periodOrder = getCSTCPeriodOrder(period.term_code, period.year_period);
                return requestedPeriodOrder === null || periodOrder === null || periodOrder <= requestedPeriodOrder;
            });

            // The API returns periods in descending order.  Use the closest published
            // period, or the newest one when the requested period falls outside cache.
            startIndex = closestAvailableIndex === -1 ? 0 : closestAvailableIndex;
            const resolvedPeriod = titleData[startIndex];

            if (yearSelect && [...yearSelect.options].some(option => option.value === String(resolvedPeriod.year_period))) {
                yearSelect.value = String(resolvedPeriod.year_period);
            }
            periodBtns.forEach(button => button.classList.toggle('active', button.textContent.trim() === resolvedPeriod.term_code));
            console.info(`CSTC ${currentTicker}: ${selectedTerm}/${selectedYear} chưa công bố; hiển thị ${resolvedPeriod.term_code}/${resolvedPeriod.year_period}.`);
        }

        const countSelect = periodCountSelect ? periodCountSelect.value : '5';
        const limit = countSelect === 'all' ? titleData.length - startIndex : parseInt(countSelect);
        const periods = titleData.slice(startIndex, startIndex + limit);

        // 1. Table Headers & 4 Yuanta Meta Rows
        let theadHtml = `<tr><th>Chỉ tiêu tài chính</th>`;
        periods.forEach(p => {
            const headerText = p.term_code === 'Năm' ? p.year_period : `${p.term_code}/${p.year_period}`;
            theadHtml += `<th>${headerText}</th>`;
        });
        theadHtml += `</tr>`;

        theadHtml += `<tr class="meta-row"><td>Giai đoạn</td>`;
        periods.forEach(p => {
            const bStr = String(p.period_begin);
            const eStr = String(p.period_end);
            theadHtml += `<td>${bStr.slice(0,4)}/${bStr.slice(4,6)}-${eStr.slice(0,4)}/${eStr.slice(4,6)}</td>`;
        });
        theadHtml += `</tr>`;

        theadHtml += `<tr class="meta-row"><td>Hợp nhất</td>`;
        periods.forEach(p => {
            theadHtml += `<td>${p.united || 'Hợp nhất'}</td>`;
        });
        theadHtml += `</tr>`;

        theadHtml += `<tr class="meta-row"><td>Kiểm toán</td>`;
        periods.forEach(p => {
            theadHtml += `<td>${p.audited_status || 'Chưa kiểm toán'}</td>`;
        });
        theadHtml += `</tr>`;

        tableHead.innerHTML = theadHtml;

        // 2. Table Body from Yuanta Detail Ratio Groups
        let tbodyHtml = '';
        detailData.forEach(group => {
            const groupName = group.report_component_name || "Nhóm chỉ số";
            tbodyHtml += `<tr class="row-group"><td colspan="${periods.length + 1}"><strong>${groupName}</strong></td></tr>`;
            
            const items = group.data || [];
            items.forEach(item => {
                tbodyHtml += `<tr>`;
                tbodyHtml += `<td style="color: var(--text-primary); font-weight: 500;">${item.field_name}</td>`;
                
                for (let idx = 0; idx < periods.length; idx++) {
                    const dataIdx = startIndex + idx;
                    const val = (item.value && item.value[dataIdx] !== undefined) ? item.value[dataIdx] : null;
                    tbodyHtml += `<td>${formatDec(val, 2)}</td>`;
                }
                tbodyHtml += `</tr>`;
            });
        });

        tableBody.innerHTML = tbodyHtml;
    }

    function getCSTCPeriodOrder(termCode, yearPeriod) {
        const year = Number(yearPeriod);
        const quarterMatch = /^Q([1-4])$/.exec(String(termCode || '').trim());
        if (!Number.isFinite(year)) return null;
        if (quarterMatch) return year * 4 + Number(quarterMatch[1]);
        if (String(termCode || '').trim() === 'Năm') return year * 4 + 4;
        return null;
    }

    async function fetchLiveCSTC(ticker) {
        if (tableBody) tableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 3rem; color: var(--primary);">⚡ Đang kết nối trực tiếp đến API Yuanta (Chỉ số tài chính CSTC) cho mã ${ticker}...</td></tr>`;
        try {
            const selectedPeriodBtn = document.querySelector('.period-btn.active');
            const term = selectedPeriodBtn ? selectedPeriodBtn.textContent.trim() : 'Q2';
            const year = yearSelect ? yearSelect.value : '2026';

            // The public Yuanta API is free, but it only permits browser requests from
            // Yuanta's own origin.  When this dashboard is served by server.py, use its
            // same-origin proxy; opening index.html directly still uses the offline cache.
            const query = new URLSearchParams({ stock_code: ticker, term_code: term, year_period: year });
            const endpoint = window.location.protocol === 'file:'
                ? `https://ysradarapi.yuanta.com.vn/api/v3/vietstock/financial_statement/report?lang=vi&page_index=1&page_size=6&report_term_type=2&report_type=CSTC&stock_code=${encodeURIComponent(ticker)}&term_code=${encodeURIComponent(term)}&unit=1000000&year_period=${encodeURIComponent(year)}`
                : `/api/yuanta/cstc?${query.toString()}`;
            const resp = await fetch(endpoint);
            if (resp.ok) {
                const json = await resp.json();
                if (json.success && json.response) {
                    window.YUANTA_CSTC_DATA = window.YUANTA_CSTC_DATA || {};
                    json.response._isLiveFallback = true;
                    // Store the proxy response under the requested ticker only.
                    window.YUANTA_CSTC_DATA[ticker] = json.response;
                    if (currentTicker === ticker) renderCSTCTable();
                    return;
                }
            }
        } catch (e) {
            console.warn(`Không thể tải CSTC trực tiếp cho ${ticker}.`, e);
        }
        if (tableBody) tableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2rem;">Chưa có chỉ số tài chính trong cache cho mã ${ticker}. Để tải trực tiếp từ API Yuanta miễn phí, hãy mở dashboard bằng <code>python dashboard/server.py</code> thay vì mở file HTML trực tiếp.</td></tr>`;
    }

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
        
        tableHead.innerHTML = ``;
        
        // Define which charts to show in the grid
        const baseKeys = [
            'net_revenue', 'net_profit', 'valuation', 
            'equity', 'structure_asset', 'profit_margin',
            'equity_used_ratio', 'accounting_balance', 'asset',
            'cash_flow', 'liquidity_ability'
        ];
        
        const layoutKeys = baseKeys.map(k => `${k}_${activeChartPeriod}`);

        let html = `<tr><td style="padding: 1rem;"><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; background: var(--bg-main);">`;
        
        layoutKeys.forEach(key => {
            if (chartData[key]) {
                const chartName = chartData[key].title.chart_name || 'Biểu đồ';
                html += `
                    <div class="glass-panel chart-panel-wrapper" style="padding: 1rem; position: relative; min-width: 0; overflow: hidden;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem; font-size: 0.95rem; display: flex; justify-content: space-between;">
                            ${chartName}
                            <div style="cursor: pointer;" class="btn-fullscreen" title="Toàn màn hình">
                                <i class="fas fa-expand" style="color: var(--text-secondary);"></i>
                            </div>
                        </h4>
                        <div id="echart-${key}" style="width: 100%; height: 400px; background: var(--bg-panel);"></div>
                    </div>
                `;
            }
        });
        
        html += `</div></td></tr>`;
        tableBody.innerHTML = html;

        // Initialize ECharts instances and Fullscreen events
        layoutKeys.forEach(key => {
            if (chartData[key]) {
                const domId = `echart-${key}`;
                initEChart(domId, chartData[key]);
                
                const dom = document.getElementById(domId);
                if (dom) {
                    const wrapper = dom.closest('.chart-panel-wrapper');
                    const btnFull = wrapper.querySelector('.btn-fullscreen');
                    if (btnFull && wrapper) {
                        btnFull.addEventListener('click', () => {
                            if (!document.fullscreenElement) {
                                wrapper.requestFullscreen().catch(err => {
                                    console.error(`Error attempting to enable fullscreen: ${err.message}`);
                                });
                            } else {
                                document.exitFullscreen();
                            }
                        });
                    }
                }
            }
        });
    }

    // Handle resize for Echarts when window resizes or fullscreen toggles
    window.addEventListener('resize', () => {
        chartInstances.forEach(chart => chart.resize());
    });
    
    document.addEventListener('fullscreenchange', () => {
        // Add a slight delay to allow the browser to complete the layout shift before resizing
        setTimeout(() => {
            chartInstances.forEach(chart => chart.resize());
        }, 100);
    });

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

        // Scan for value_1 up to value_10
        for (let i = 1; i <= 10; i++) {
            const vKey = `value_${i}`;
            if (titleObj[vKey]) {
                const sName = titleObj[vKey];
                const sUnit = unitObj[vKey] || '';
                
                let sType = 'line';
                let stackVal = undefined;
                
                if (elementId.includes('net_revenue') || elementId.includes('net_profit')) {
                    if (i === 1) sType = 'bar';
                } else if (elementId.includes('accounting_balance') || elementId.includes('asset') || elementId.includes('structure_asset')) {
                    sType = 'bar';
                    stackVal = 'total';
                } else if (elementId.includes('cash_flow')) {
                    if (i <= 3) {
                        sType = 'bar';
                        stackVal = 'total';
                    } else {
                        sType = 'line';
                    }
                } else if (elementId.includes('liquidity_ability')) {
                    sType = 'bar';
                    if (i === 1 || i === 2) {
                        stackVal = 'debt';
                    } else {
                        stackVal = 'equity';
                    }
                }
                
                const yIndex = (sUnit === '%' || sUnit === 'Lần' || sUnit === 'Ngày') ? 1 : 0;
                yAxisIds.add(yIndex);
                
                legendData.push(sName);
                seriesData.push({
                    name: sName,
                    type: sType,
                    stack: stackVal,
                    yAxisIndex: yIndex,
                    smooth: true,
                    showSymbol: false,
                    data: rawData.map(d => d[vKey] !== undefined ? d[vKey] : null),
                    tooltip: { valueFormatter: value => value ? `${value} ${sUnit}` : '-' }
                });
            }
        }

        const yAxes = [];
        if (yAxisIds.has(0)) {
            yAxes.push({ type: 'value', name: '', splitLine: { show: false } });
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
            legend: { type: 'scroll', data: legendData, bottom: 0, textStyle: { color: '#aaa', fontSize: 11 }, pageTextStyle: { color: '#aaa' }, pageIconColor: '#aaa', pageIconInactiveColor: '#444' },
            grid: { left: '3%', right: '3%', bottom: '20%', top: '10%', containLabel: true },
            xAxis: [ { type: 'category', data: times, axisLabel: { color: '#888', fontSize: 10, rotate: 45 } } ],
            yAxis: yAxes,
            series: seriesData,
            color: ['#8b5cf6', '#f97316', '#10b981', '#3b82f6', '#ec4899']
        };

        myChart.setOption(option);
    }


    // =========================================================
    // EVENTS TAB (TIN TỨC & SỰ KIỆN)
    // =========================================================
    function renderEvents(ticker) {
        const eventsBody = document.getElementById('events-body');
        if (!eventsBody) return;
        
        if (!window.YUANTA_EVENTS_DATA || !window.YUANTA_EVENTS_DATA[ticker] || window.YUANTA_EVENTS_DATA[ticker].length === 0) {
            eventsBody.innerHTML = `<tr><td style="text-align: center; padding: 2rem; color: var(--text-secondary);">Chưa có sự kiện nào trong hệ thống (từ 01/2025) cho mã ${ticker}.</td></tr>`;
            return;
        }

        const events = window.YUANTA_EVENTS_DATA[ticker];
        
        let html = '';
        events.forEach(ev => {
            let icon = 'fas fa-calendar-alt';
            let color = 'var(--text-secondary)';
            if (ev.Type === 'cash_dividend') { icon = 'fas fa-money-bill-wave'; color = '#10b981'; }
            else if (ev.Type === 'stock_dividend' || ev.Type === 'stock_bonus') { icon = 'fas fa-cubes'; color = '#8b5cf6'; }
            else if (ev.Type === 'annual_meeting') { icon = 'fas fa-users'; color = '#3b82f6'; }
            
            html += `
                <tr>
                    <td style="padding: 1.5rem; border-bottom: 1px solid var(--border-color);">
                        <div style="display: flex; align-items: flex-start; gap: 1rem;">
                            <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; color: ${color}; font-size: 1.2rem;">
                                <i class="${icon}"></i>
                            </div>
                            <div>
                                <h4 style="color: var(--text-primary); margin-bottom: 0.5rem; font-size: 1.05rem;">${ev.Content || 'Sự kiện doanh nghiệp'}</h4>
                                <div style="display: flex; gap: 1.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                                    <span><strong>Ngày GDKHQ:</strong> ${ev.ExRightDate || '-'}</span>
                                    <span><strong>Ngày đăng ký:</strong> ${ev.RecordDate || '-'}</span>
                                    <span><strong>Ngày thực hiện:</strong> ${ev.EffectiveDate || '-'}</span>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        });
        
        eventsBody.innerHTML = html;
    }

    function formatNumber(val, scale) {
        if (val === null || val === undefined || val === '') return '-';
        const scaledVal = parseFloat(val) / parseFloat(scale);
        if (isNaN(scaledVal)) return '-';
        return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(scaledVal);
    }

    function renderTable() {
        if (!currentTicker || !window.BCTC_DATA || !window.BCTC_DATA[currentTicker]) {
            if (tableBody) tableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 2rem;">Chưa có dữ liệu Báo cáo tài chính chi tiết cho mã ${currentTicker} trong Cache.</td></tr>`;
            return;
        }
        
        const data = window.BCTC_DATA[currentTicker];
        const allPeriods = window.PERIODS || [];
        
        const countSelect = periodCountSelect.value;
        const count = countSelect === 'all' ? allPeriods.length : parseInt(countSelect);
        
        const activePeriodFilter = document.querySelector('.period-btn.active') ? document.querySelector('.period-btn.active').textContent.trim() : 'Q4';
        const selectedYear = parseInt(yearSelect.value || "2025");
        
        let displayPeriods = [];
        
        if (activePeriodFilter === 'Năm') {
            for (let i = 0; i < count; i++) {
                const y = selectedYear - i;
                displayPeriods.push({ label: y.toString(), type: 'year', year: y });
            }
        } else {
            const targetPeriod = `${selectedYear}_${activePeriodFilter}`;
            let startIndex = allPeriods.findIndex(p => p === targetPeriod);
            if (startIndex === -1) startIndex = 0;
            
            const slice = allPeriods.slice(startIndex, startIndex + count);
            displayPeriods = slice.map(p => {
                const parts = p.split('_');
                return { label: `${parts[1]}/${parts[0]}`, type: 'quarter', year: parseInt(parts[0]), quarter: parseInt(parts[1].replace('Q', '')), originalKey: p };
            });
        }
        
        let theadHtml = `<tr><th>Chỉ tiêu tài chính</th>`;
        displayPeriods.forEach(p => { theadHtml += `<th>${p.label}</th>`; });
        theadHtml += `</tr>`;
        
        theadHtml += `<tr class="meta-row"><td>Giai đoạn</td>`;
        displayPeriods.forEach(p => {
            if (p.type === 'year') {
                theadHtml += `<td>${p.year}/01-${p.year}/12</td>`;
            } else {
                const sm = (p.quarter - 1) * 3 + 1;
                const em = p.quarter * 3;
                theadHtml += `<td>${p.year}/${sm.toString().padStart(2, '0')}-${p.year}/${em.toString().padStart(2, '0')}</td>`;
            }
        });
        theadHtml += `</tr>`;
        
        theadHtml += `<tr class="meta-row"><td>Hợp nhất</td>`;
        displayPeriods.forEach(() => theadHtml += `<td>Hợp nhất</td>`);
        theadHtml += `</tr>`;
        
        theadHtml += `<tr class="meta-row"><td>Kiểm toán</td>`;
        displayPeriods.forEach(p => {
            theadHtml += `<td>${p.type === 'year' ? 'Kiểm toán' : (p.quarter === 2 ? 'Soát xét' : 'Chưa kiểm toán')}</td>`;
        });
        theadHtml += `</tr>`;
        
        tableHead.innerHTML = theadHtml;
        
        let tbodyHtml = '';
        const scale = unitScaleSelect.value;
        const componentOrder = ["Kết quả kinh doanh", "Cân đối kế toán", "Lưu chuyển tiền tệ", "Chỉ số tài chính"];
        
        componentOrder.forEach(compName => {
            if (data[compName] && data[compName].length > 0) {
                tbodyHtml += `<tr class="row-group"><td colspan="${displayPeriods.length + 1}">✨ ${compName}</td></tr>`;
                data[compName].forEach(item => {
                    tbodyHtml += `<tr><td>${item.field}</td>`;
                    displayPeriods.forEach(p => {
                        let val = null;
                        if (p.type === 'year') {
                            if (compName === "Kết quả kinh doanh" || compName === "Lưu chuyển tiền tệ") {
                                const q1 = parseFloat(item[`${p.year}_Q1`]);
                                const q2 = parseFloat(item[`${p.year}_Q2`]);
                                const q3 = parseFloat(item[`${p.year}_Q3`]);
                                const q4 = parseFloat(item[`${p.year}_Q4`]);
                                if (!isNaN(q1) || !isNaN(q2) || !isNaN(q3) || !isNaN(q4)) {
                                    val = (q1 || 0) + (q2 || 0) + (q3 || 0) + (q4 || 0);
                                }
                            } else {
                                val = item[`${p.year}_Q4`];
                            }
                        } else {
                            val = item[p.originalKey];
                        }
                        const currentScale = (compName === "Chỉ số tài chính") ? 1 : scale;
                        tbodyHtml += `<td>${formatNumber(val, currentScale)}</td>`;
                    });
                    tbodyHtml += `</tr>`;
                });
            }
        });
        
        tableBody.innerHTML = tbodyHtml;
    }

    // ==========================================
    // TRADING DATA (Lịch sử giá & Giao dịch nước ngoài)
    // ==========================================
    const tradingFromDate = document.getElementById('trading-from-date');
    const tradingToDate = document.getElementById('trading-to-date');
    const tradingTbody = document.getElementById('trading-tbody');
    const tradingForeignTbody = document.getElementById('trading-foreign-tbody');
    const tradingSubTabs = document.querySelectorAll('.trading-sub-tab');
    const tradingContents = document.querySelectorAll('.trading-content');
    
    // Tab switching for trading sub-tabs
    tradingSubTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tradingSubTabs.forEach(t => {
                t.classList.remove('active');
                t.style.background = 'transparent';
                t.style.color = '#4b5563';
                t.style.border = '1px solid #e5e7eb';
            });
            tradingContents.forEach(c => c.classList.add('hidden'));
            
            tab.classList.add('active');
            tab.style.background = '#8b5cf6';
            tab.style.color = 'white';
            tab.style.border = 'none';
            
            const target = document.getElementById(tab.getAttribute('data-target'));
            if (target) {
                target.classList.remove('hidden');
            }
            
            if (currentTicker) {
                renderTrading(currentTicker);
            }
        });
    });

    // Set default dates (30 days range)
    const today = new Date();
    const last30Days = new Date();
    last30Days.setDate(today.getDate() - 30);
    
    if (tradingToDate && !tradingToDate.value) {
        tradingToDate.value = today.toISOString().split('T')[0];
    }
    if (tradingFromDate && !tradingFromDate.value) {
        tradingFromDate.value = last30Days.toISOString().split('T')[0];
    }

    // ── Static JSON.gz Cache (session-scoped, tránh tải lại khi đổi sub-tab) ──
    const _historyCache = {};

    /**
     * Load history từ per-ticker JSON.gz static file.
     * File được tạo bởi: python scripts/download_history.py + build_static_files.py
     * Path: data/static/history/{TICKER}.json.gz
     *
     * Returns object { ohlcv: [...], foreign: [...], fields_ohlcv, fields_foreign }
     * Trả về null nếu file không tồn tại hoặc lỗi.
     */
    async function loadTickerHistoryFromStatic(ticker) {
        const code = ticker.toUpperCase();
        if (_historyCache[code]) return _historyCache[code];

        // Sử dụng APP_CONFIG.BASE_URL thay cho đường dẫn tương đối
        const url = `${APP_CONFIG.BASE_URL}/history/${code}.json.gz`;

        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;

            let data;
            // GitHub Pages tự serve .gz với Content-Encoding: gzip → browser auto-decompress
            // Khi mở bằng file:// thì server không set header → cần decompress thủ công
            const contentEncoding = resp.headers.get('content-encoding');
            if (contentEncoding && contentEncoding.includes('gzip')) {
                // Browser đã decompress tự động
                data = await resp.json();
            } else {
                // file:// protocol: dùng DecompressionStream (Chrome 80+)
                const blob = await resp.blob();
                if (typeof DecompressionStream !== 'undefined') {
                    const ds = new DecompressionStream('gzip');
                    const stream = blob.stream().pipeThrough(ds);
                    const text = await new Response(stream).text();
                    data = JSON.parse(text);
                } else {
                    // Fallback: thử parse trực tiếp (nếu browser đã decompress ngầm)
                    const text = await resp.text();
                    data = JSON.parse(text);
                }
            }

            _historyCache[code] = data;
            return data;
        } catch (err) {
            console.warn(`[History] ${code}: ${err.message}`);
            return null;
        }
    }

    /**
     * Lọc dữ liệu theo khoảng ngày.
     * rows: array-of-arrays, cột đầu tiên (index 0) là date string "YYYY-MM-DD".
     */
    function filterByDateRange(rows, fromDate, toDate) {
        if (!fromDate && !toDate) return rows;
        return rows.filter(row => {
            const d = row[0];
            return (!fromDate || d >= fromDate) && (!toDate || d <= toDate);
        });
    }

    /**
     * Render bảng Lịch sử giá từ dữ liệu static.
     * Thay thế hoàn toàn fetchTradingData (không cần serve_dashboard.py).
     */
    async function fetchTradingData(ticker, fromDate, toDate) {
        if (!tradingTbody) return;
        tradingTbody.innerHTML = '<tr><td colspan="13" style="text-align:center; padding: 20px;">Đang tải dữ liệu...</td></tr>';

        const data = await loadTickerHistoryFromStatic(ticker);

        if (!data || !data.ohlcv || data.ohlcv.length === 0) {
            tradingTbody.innerHTML = `
                <tr><td colspan="13" style="text-align:center; padding: 30px;">
                    <div style="color: #f59e0b; font-weight: 600; margin-bottom: 8px;">⚠️ Chưa có dữ liệu offline cho ${ticker}</div>
                    <div style="color: var(--text-secondary); font-size: 0.88rem;">
                        Chạy lệnh sau để tải về máy:<br>
                        <code style="background: var(--bg-card); padding: 4px 8px; border-radius: 4px; margin-top: 6px; display: inline-block;">
                            python scripts/download_history.py --tickers ${ticker}
                        </code>
                    </div>
                </td></tr>`;
            return;
        }

        // Lấy index của từng field
        const fi = {};
        (data.fields_ohlcv || []).forEach((f, i) => fi[f] = i);
        // fields_ohlcv: ["date","open","high","low","close","volume","value_m","pct_change"]

        // Lọc theo ngày và sắp xếp giảm dần (ngày mới nhất lên trên)
        const filtered = filterByDateRange(data.ohlcv, fromDate, toDate)
            .slice().reverse();

        if (filtered.length === 0) {
            tradingTbody.innerHTML = '<tr><td colspan="13" style="text-align:center; padding: 20px;">Không có dữ liệu trong khoảng thời gian này</td></tr>';
            return;
        }

        let html = '';
        filtered.forEach(row => {
            const dateStr  = row[fi['date']] || '';
            const dateParts = dateStr.split('-');
            const fmtDate  = dateParts.length === 3 ? `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}` : dateStr;

            const pct     = parseFloat(row[fi['pct_change']] || 0);
            const pctColor = pct > 0 ? '#10b981' : pct < 0 ? '#ef4444' : '#f59e0b';
            const pctPrefix = pct > 0 ? '+' : '';

            const close   = row[fi['close']]   || 0;
            const open    = row[fi['open']]    || 0;
            const high    = row[fi['high']]    || 0;
            const low     = row[fi['low']]     || 0;
            const avg     = row[fi['average']] || 0;
            const vol     = row[fi['volume']]  || 0;
            const valM    = row[fi['value_m']] || 0;  // da la trieu VND

            const ftBuy  = row[fi['ft_buy_vol']] || 0;
            const ftSell = row[fi['ft_sell_vol']] || 0;
            const ptVol  = row[fi['pt_vol']] || 0;
            const ptValM = row[fi['pt_val_m']] || 0;

            html += `
                <tr>
                    <td style="text-align:center; font-weight:500; color:var(--primary-color);">${fmtDate}</td>
                    <td style="color:${pctColor}; font-weight:600;">${pctPrefix}${formatDec(pct, 2)}%</td>
                    <td style="color:${pctColor}; font-weight:600;">${formatInt(close)}</td>
                    <td>${formatInt(open)}</td>
                    <td>${formatInt(high)}</td>
                    <td>${formatInt(low)}</td>
                    <td>${formatInt(avg)}</td>
                    <td>${formatInt(vol)}</td>
                    <td>${formatInt(valM)}</td>
                    <td>${formatInt(ftBuy)}</td>
                    <td>${formatInt(ftSell)}</td>
                    <td>${formatInt(ptVol)}</td>
                    <td>${formatInt(ptValM)}</td>
                </tr>`;
        });
        tradingTbody.innerHTML = html;
    }

    /**
     * Render bảng Giao dịch nước ngoài từ dữ liệu static.
     * Thay thế hoàn toàn fetchForeignTradingData (không cần serve_dashboard.py).
     */
    async function fetchForeignTradingData(ticker, fromDate, toDate) {
        if (!tradingForeignTbody) return;
        tradingForeignTbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Đang tải dữ liệu...</td></tr>';

        const data = await loadTickerHistoryFromStatic(ticker);

        if (!data || !data.foreign || data.foreign.length === 0) {
            tradingForeignTbody.innerHTML = `
                <tr><td colspan="10" style="text-align:center; padding: 30px;">
                    <div style="color: #f59e0b; font-weight: 600; margin-bottom: 8px;">⚠️ Chưa có dữ liệu offline cho ${ticker}</div>
                    <div style="color: var(--text-secondary); font-size: 0.88rem;">
                        Chạy lệnh sau để tải về máy:<br>
                        <code style="background: var(--bg-card); padding: 4px 8px; border-radius: 4px; margin-top: 6px; display: inline-block;">
                            python scripts/download_history.py --tickers ${ticker}
                        </code>
                    </div>
                </td></tr>`;
            return;
        }

        // fields_foreign: ["date","ft_buy_vol","ft_sell_vol","ft_net_vol","ft_net_val_ty","ft_val_rate","ft_owned_rate"]
        const fi = {};
        (data.fields_foreign || []).forEach((f, i) => fi[f] = i);

        const filtered = filterByDateRange(data.foreign, fromDate, toDate)
            .slice().reverse();

        if (filtered.length === 0) {
            tradingForeignTbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Không có dữ liệu trong khoảng thời gian này</td></tr>';
            return;
        }

        let html = '';
        filtered.forEach(row => {
            const dateStr  = row[fi['date']] || '';
            const dateParts = dateStr.split('-');
            const fmtDate  = dateParts.length === 3 ? `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}` : dateStr;

            const remainRoom = row[fi['remain_room']] || 0;
            const buyVol     = row[fi['ft_buy_vol']]  || 0;
            const buyValTy   = row[fi['ft_buy_val_ty']] || 0;
            const sellVol    = row[fi['ft_sell_vol']] || 0;
            const sellValTy  = row[fi['ft_sell_val_ty']] || 0;
            const netVol     = row[fi['ft_net_vol']]  || 0;
            const netValTy   = row[fi['ft_net_val_ty']] || 0;
            const valRate    = row[fi['ft_val_rate']]  || 0;
            const ownRate    = row[fi['ft_owned_rate']] || 0;

            const netColor = netVol > 0 ? '#10b981' : netVol < 0 ? '#ef4444' : '#f59e0b';

            html += `
                <tr>
                    <td style="text-align:center; font-weight:500; color:var(--primary-color);">${fmtDate}</td>
                    <td>${formatInt(remainRoom)}</td>
                    <td>${formatInt(buyVol)}</td>
                    <td>${formatDec(buyValTy, 3)} tỷ</td>
                    <td>${formatInt(sellVol)}</td>
                    <td>${formatDec(sellValTy, 3)} tỷ</td>
                    <td style="color:${netColor}; font-weight:600;">${formatInt(netVol)}</td>
                    <td style="color:${netColor};">${formatDec(netValTy, 2)} tỷ</td>
                    <td>${formatDec(valRate, 2)}%</td>
                    <td>${formatDec(ownRate, 2)}%</td>
                </tr>`;
        });
        tradingForeignTbody.innerHTML = html;
    }

    if (tradingFromDate) {
        tradingFromDate.addEventListener('change', () => {
            if (currentTicker && !document.getElementById('tab-trading').classList.contains('hidden')) {
                renderTrading(currentTicker);
            }
        });
    }
    
    if (tradingToDate) {
        tradingToDate.addEventListener('change', () => {
            if (currentTicker && !document.getElementById('tab-trading').classList.contains('hidden')) {
                renderTrading(currentTicker);
            }
        });
    }

    function renderTrading(ticker) {
        if (!tradingFromDate || !tradingToDate) return;
        const activeTab = document.querySelector('.trading-sub-tab.active');
        if (!activeTab) return;
        
        const targetId = activeTab.getAttribute('data-target');
        
        if (targetId === 'trading-price-content') {
            if (tradingTbody) tradingTbody.innerHTML = '<tr><td colspan="13" style="text-align:center; padding: 20px;">Đang tải dữ liệu...</td></tr>';
            fetchTradingData(ticker, tradingFromDate.value, tradingToDate.value);
        } else if (targetId === 'trading-foreign-content') {
            if (tradingForeignTbody) tradingForeignTbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">Đang tải dữ liệu...</td></tr>';
            fetchForeignTradingData(ticker, tradingFromDate.value, tradingToDate.value);
        }
    }

    // Initialize default showcase ticker ACB on load
    selectTicker(currentTicker);
});
