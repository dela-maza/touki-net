document.querySelectorAll('button[data-doc-label]').forEach(button => {
    button.addEventListener('click', () => {
        const label = button.getAttribute('data-doc-label');
        const titleTd = document.querySelector('td.document-title');
        const mainFrame = document.getElementById('main-frame');
        const amountLabelTd = document.getElementById('amount-label');
        const estimateDate = document.getElementById('estimate_date');
        const invoiceDate = document.getElementById('invoice_date');
        const receiptDate = document.getElementById('receipt_date');

        // --- ボタンの選択状態をリセット ---
        document.querySelectorAll(
            'button[data-doc-label]')
            .forEach(btn => btn.classList.remove('active'));
        // クリックされた自分だけ active に
        button.classList.add('active');

        if (label !== "押印" && label !== "戻る") {
            // --- 日付表示切替 ---
            estimateDate.style.display = 'none';
            invoiceDate.style.display = 'none';
            receiptDate.style.display = 'none';

            if (label.includes('見積')) {
                estimateDate.style.display = '';
            } else if (label.includes('請求')) {
                invoiceDate.style.display = '';
            } else if (label.includes('領収')) {
                receiptDate.style.display = '';
            }

            if (titleTd) titleTd.textContent = label + '書';
            if (amountLabelTd) amountLabelTd.textContent = label + '額';

            // --- ブラウザタイトルも更新 ---
            document.title = `${label}書（${clientName}殿）`;
        }

        // --- 押印の表示切替 ---
        if (label === "押印") {
            const existingImg = document.getElementById('stamp-image');
            if (existingImg && mainFrame) {
                mainFrame.removeChild(existingImg);
            } else if (mainFrame) {
                const stampImg = document.createElement('img');
                stampImg.id = 'stamp-image';
                stampImg.src = stampImageUrl;
                stampImg.alt = "押印";
                stampImg.style.position = 'absolute';
                stampImg.style.left = '780px';
                stampImg.style.top = '260px';
                stampImg.style.width = '10%';
                stampImg.style.height = 'auto';
                mainFrame.appendChild(stampImg);
            }
        } else {
            const existingImg = document.getElementById('stamp-image');
            if (existingImg) existingImg.remove();
        }
    });
});

// 初期ロード時に「見積書」ボタンをアクティブに
document.addEventListener('DOMContentLoaded', () => {
    document.title = `見積書（${clientName}殿）`;
    const estimateBtn = document.querySelector('button[data-doc-label*="見積"]');
    if (estimateBtn) estimateBtn.classList.add('active');
});