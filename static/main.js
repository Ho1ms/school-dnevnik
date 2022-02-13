if (window.location.href.indexOf('#') !== -1) {
const xhttps = new XMLHttpRequest();

    let token = window.location.href.split('#')[1].split('=')[1].slice(0, 32)
	xhttps.open('POST',window.location.origin+'/api',true)
	xhttps.send(JSON.stringify({'token':token}))

	xhttps.onreadystatechange = function () {
    	if (this.readyState === 4 && this.status === 200) {
    		window.location.replace('https://vk.com/im?sel=-205279154');
    	} else if (this.readyState === 4 && this.status === 402) {
    		console.log('Произошла ошибка!')
    	}
    }
}

