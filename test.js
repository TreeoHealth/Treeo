import fetch from 'cross-fetch';
const meetConfig = {
    apiKey: 'oURxTkQkTL6USazzprxmuw',
    meetingNumber: '123456789',
    leaveUrl: 'https://gmail.com',
    userName: 'Sophia Vaughn',
    userEmail: 'cq7614@gmail.com', // required for webinar
    passWord: 'password', // if required
    role: 1 // 1 for host; 0 for attendee or webinar
};
function getSignature(meetConfig) {
	fetch(`${https://api.zoom.us/v1/}`, { //https://api.zoom.us/v2/users/cq7614/meetings
			method: 'POST',
			body: JSON.stringify({ meetingData: meetConfig })
		})
		.then(result => result.text())
		.then(response => 
		{
			ZoomMtg.init({
				leaveUrl: meetConfig.leaveUrl,
				isSupportAV: true,
				success: function() {
					ZoomMtg.join({
						signature: response,
						apiKey: meetConfig.apiKey,
						meetingNumber: meetConfig.meetingNumber,
						userName: meetConfig.userName,
						// Email required for Webinars
						userEmail: meetConfig.userEmail, 
						// password optional; set by Host
						password: meetConfig.passWord, 
						error(res) { 
							console.log(res) 
						}
					})		
				}
			})
		}
		)
}

getSignature(meetConfig)