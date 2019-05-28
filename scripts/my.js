define(["selenium-webdriver/chrome"], function(chrome){



    
    
function log(msg){
	document.getElementById("display").value = msg;
}

function handleFailure(err, driver) {
     console.error('Something went wrong!\n', err.stack, '\n');
     driver.quit();
}

async function getHTML(url){
    log(url);
    var chrome;
    var Builder;
    var By;
    var Key
    var until;

    log("chrome is loaded");

    
    // var {Builder, By, Key, until} : function(){
    //   return s;  
    // } 

    // try{
    
    

        // var screen = {
        //   width: 640,
        //   height: 480
        // };

        // var driver = new Builder()
        //     .forBrowser('chrome')
        //     .setChromeOptions(new chrome.Options().headless().windowSize(screen))
        //     .build();
        // await driver.get(url);
        // var ret;
        // await driver.getPageSource().then(function(data) { ret = data;});
        // driver.quit();
        // log(ret);
    // }
    // catch(err){
    //     handleFailure(err, driver)
    // }
}

// var url = 'http://crossbrowsertesting.github.io/selenium_example_page.html';
// url = 'https://www.snopes.com/fact-check/ban-oktoberfest-petition/';
// getHTML(url);

});