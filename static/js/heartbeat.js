setInterval(function() {
    fetch('/heartbeat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: "{{ user.id }}" })
    });
}, 300000); // 每5分钟发送一次请求
