const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + require('path').resolve(__dirname, '../..') + '/docs/report/report.html', { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: '' + require('path').resolve(__dirname, '../..') + '/docs/Easter Morning Report.pdf', format: 'A4',
    printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;text-align:center;font-family:serif;font-size:8pt;color:#000;"><span class="pageNumber"></span></div>' });
  await b.close();
})();
