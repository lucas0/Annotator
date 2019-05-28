
function log(msg){
	document.getElementById("display").innerHTML = msg;
}

async function getTitle(url){
    try{
	const chrome = require('selenium-webdriver/chrome');
	const {Builder, By, Key, until} = require('selenium-webdriver');
	const screen = {
	  width: 640,
	  height: 480
	};
	let driver = new Builder()
	    .forBrowser('chrome')
	    .setChromeOptions(new chrome.Options().headless().windowSize(screen))
	    .setFirefoxOptions(new firefox.Options().headless().windowSize(screen))
	    .build();

	await driver.getTitle().then(function(title) {
                    console.log("The title is: " + title)
            });
        driver.quit();
    }
    catch(err){
        handleFailure(err, driver)
    }
}

async function getHTML(url){
    try{
        await driver.get(url);
	var source = driver.getPageSource();
        driver.quit();
	return source;
    }
    catch(err){
        handleFailure(err, driver)
    }
}

var url = 'http://crossbrowsertesting.github.io/selenium_example_page.html';
console.log(getTitle(url));

function handleFailure(err, driver) {
     console.error('Something went wrong!\n', err.stack, '\n');
     driver.quit();
} 
