// amount_document/stat/js/amount_document_ui.js
document.querySelectorAll('button[data-doc-label]').forEach(button => {
    button.addEventListener('click', () => {
        const label = button.getAttribute('data-doc-label');
        const titleTd = document.querySelector('td.document-title');
        const mainFrame = document.getElementById('main-frame');
        const amountLabelTd = document.getElementById('amount-label');  // 金額ラベル
        const estimateDate = document.getElementById('estimate_date');  // 日付表示のdivなど
        const invoiceDate = document.getElementById('invoice_date');
        const receiptDate = document.getElementById('receipt_date');

        // 一旦全部非表示にする
        estimateDate.style.display = 'none';
        invoiceDate.style.display = 'none';
        receiptDate.style.display = 'none';

        // 押されたボタンに応じて表示切替
        if (label.includes('見積')) {
            estimateDate.style.display = '';
        } else if (label.includes('請求')) {
            invoiceDate.style.display = '';
        } else if (label.includes('領収')) {
            receiptDate.style.display = '';
        }

        // タイトルと金額ラベルの更新（押印・戻る以外）
        if (label !== "押印" && label !== "戻る") {
            if (titleTd) {
                titleTd.textContent = label + '書';
            }
            if (amountLabelTd) {
                amountLabelTd.textContent = label + '額';
            }

            // 日付表示切替
            if (estimateDate && invoiceDate && receiptDate) {
                estimateDate.style.display = label.includes('見積') ? 'table-row' : 'none';
                invoiceDate.style.display = label.includes('請求') ? 'table-row' : 'none';
                receiptDate.style.display = label.includes('領収') ? 'table-row' : 'none';
            }
        }

        // 押印の表示・非表示トグル
        if (label === "押印") {
            const existingImg = document.getElementById('stamp-image');
            if (existingImg && mainFrame) {
                mainFrame.removeChild(existingImg);
            } else if (mainFrame) {
                const stampImg = document.createElement('img');
                stampImg.id = 'stamp-image';
                stampImg.src = stampImageUrl;  // Jinjaから渡されたURL
                stampImg.alt = "押印";
                stampImg.style.position = 'absolute';
                stampImg.style.left = '840px';
                stampImg.style.top = '210px';
                stampImg.style.width = '10%';
                stampImg.style.height = 'auto';
                mainFrame.appendChild(stampImg);
            }
        } else {
            // 押印以外は画像削除
            const existingImg = document.getElementById('stamp-image');
            if (existingImg) {
                existingImg.remove();
            }
        }

        // 戻るボタンの処理
        // if (label === "戻る") {
        //     window.history.back();
        // }
    });
});