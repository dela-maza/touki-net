
//window.addEventListener('load',function(){
//  // 処理内容を記述
//
//
//const studentName =document.getElementsByClassName("ref");
//alert(studentName[0])
//const studentNames = Array.from(studentName);
//
//studentNames.forEach(function(student_name) {
//  student_name.addEventListener("click", function() {
//  student_name.style.color='#fff'
//});
event.stopPropagation()
event.stopImmediatePropagation()
//マウスオーバー時の処理を記述
function over(id){

  let elm = document.getElementById(id).parentElement;
  elm.style.cssText = 'display:block';
  elm.style.top = event.clientY + window.pageYOffset + 'px';
   elm.style.left = event.clientX + window.pageXOffset + 'px';
//   elm.style.width='700px';
//   elm.style.height='700px';
//alert(elm.style.offsetTop);


//alert(window.pageYOffset )


}
function out(id){

let elm = document.getElementById(id).parentElement;
//elm.style.offsetTop = (0)+'px';
//alert(elm.id);
//elm.style.top = event.clientY + window.pageYOffset + 'px';

// elm.style.width='10px';
//   elm.style.height='10px';
 elm.style.cssText = 'display:none';

//   elm.style.left = '0p;'
//  elm.style.width='700px';
  }
//  elem.parentElement.style.display= 'block';
//  elm.style.color = "red"; // テキストの色を変更する
//    window.open(
//        "https://programmercollege.jp/",
//        "_blank",
//        "menubar=0,width=300,height=200,top=100,left=100"
//    );
//     nwin = window.open("", "", 'width=200,height=1300,left=2100,top=200');
//	nwin.document.open();
//	nwin.document.write("<HTML><HEAD>");
//	nwin.document.write("<TITLE>New one</TITLE>");
//	nwin.document.writeln("<BODY>");
//	nwin.document.write('clientX: ' + e.clientX);
//	nwin.document.write("</BODY></HTML>");
//	nwin.document.close();

//alert(event.screenX)


//マウスアウト時の処理を記述



//sc = '''<button onClick="getElements();">要素を取得</button>
//<style>
//const targets = document.getElementsByClassName("article");
//const popups = document.getElementById("ref_article");
//
//// ボタンにhoverした時
//target.addEventListener('mouseover', () => {
//  popup.style.display = 'block';
//}, false);
//
//// ボタンから離れた時
//target.addEventListener('mouseleave', () => {
//  popup.style.display = 'none';
//}, false);


//
//
//  body {
//    width: 540px;
//  }
//
//  #box {
//    border: 2px solid blue;
//    height: 1000px;
//  }
//
//  p {
//    padding: 10px;
//  }
//</style>
//
//<h2>座標を取得する</h2>
//<div id="box">
//  <p>Click here □</p>
//</div>
//
//<script>
//
//let box = document.getElementById('box');
//box.addEventListener('click', e => {
//  console.log('clientX: ' + e.clientX);
//  console.log('clientY: ' + e.clientY);
//  console.log('pageX: ' + e.pageX);
//  console.log('pageY: ' + e.pageY);
//  nwin = window.open("", "", 'width=200,height=1300,left=2100,top=200');
//	nwin.document.open();
//	nwin.document.write("<HTML><HEAD>");
//	nwin.document.write("<TITLE>New one</TITLE>");
//	nwin.document.writeln("<BODY>");
//	nwin.document.write('clientX: ' + e.clientX);
//	nwin.document.write("</BODY></HTML>");
//	nwin.document.close();
//});
//function getElements(){
//    let elements = document.getElementsByClassName('article');
//    let len = elements.length;
//    for (let i = 0; i < len; i++){
//        elements.item(i).style.border="2px solid #0000ff";
//    }
//    nwin = window.open("", "", 'width=200,height=1300,left=2100,top=200');
//	nwin.document.open();
//	nwin.document.write("<HTML><HEAD>");
//	nwin.document.write("<TITLE>New one</TITLE>");
//	nwin.document.writeln("<BODY>");
//	nwin.document.write(elements.item(0).innerHTML);
//	nwin.document.write("</BODY></HTML>");
//	nwin.document.close();
//}
//</script>'''