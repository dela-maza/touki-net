// amount_document/stat/js/amount_document_ui.js
document.querySelectorAll('button[data-doc-label]').forEach(button => {
    button.addEventListener('click', () => {
        const label = button.getAttribute('data-doc-label');
        const titleTd = document.querySelector('td.document-title');
        const mainFrame = document.getElementById('main-frame');

        if (label !== "押印") {
            if (titleTd) {
                titleTd.textContent = label;
            }
        }

        if (label === "押印") {
            const existingImg = document.getElementById('stamp-image');
            if (existingImg && mainFrame) {
                // 画像がある場合は削除（トグル動作）
                mainFrame.removeChild(existingImg);
            } else if (mainFrame) {
                // 画像がない場合は新規追加
                const stampImg = document.createElement('img');
                stampImg.id = 'stamp-image';
                stampImg.src = stampImageUrl;  // Jinjaから渡されたURL
                stampImg.alt = "押印";
                stampImg.style.position = 'absolute';
                stampImg.style.left = '840px';
                stampImg.style.top = '210px';
                stampImg.style.width = '10%';  // 5%サイズ
                stampImg.style.height = 'auto';  // 高さは自動調整
                mainFrame.appendChild(stampImg);
            }
        } else {
            // 押印以外は画像を削除
            const existingImg = document.getElementById('stamp-image');
            if (existingImg) {
                existingImg.remove();
            }
        }
        if (label === "戻る") {
            window.history.back();  // ブラウザの戻る動作
        }
    });
});
