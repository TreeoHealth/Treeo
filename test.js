const meetConfig = {
    apiKey: '3239845720934223459'
    meetingNumber: '123456789',
    leaveUrl: 'https://yoursite.com/meetingEnd',
    userName: 'Firstname Lastname',
    userEmail: 'firstname.lastname@yoursite.com', // required for webinar
    passWord: 'password', // if required
    role: 1 // 1 for host; 0 for attendee or webinar
};
getSignature(meetConfig) {
	fetch(`${YOUR_SIGNATURE_ENDPOINT}`, {
			method: 'POST',
			body: JSON.stringify({ meetingData: meetConfig })
		})
		.then(result => result.text())
		.then(response => {
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
						password: meetConfig.passWord 
						error(res) { 
							console.log(res) 
						}
					})		
				}
			})
	}
}