def test_monthly_pdf_report_api_and_download(client):
    # 1. Login as admin
    admin_login = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    assert admin_login.status_code == 200
    token = admin_login.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Trigger on-demand PDF report generation
    gen_res = client.post('/api/v1/admin/reports/generate', headers=headers)
    assert gen_res.status_code == 200
    data = gen_res.get_json()
    assert 'PDF' in data['message'] or 'pdf_file' in data
    assert 'pdf_file' in data
    pdf_filename = data['pdf_file']
    assert pdf_filename.endswith('.pdf')

    # 3. Download the specific generated PDF
    dl_res = client.get(f'/api/v1/admin/reports/download/{pdf_filename}', headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.mimetype == 'application/pdf'
    assert len(dl_res.data) > 500  # Valid PDF binary data
    assert dl_res.data.startswith(b'%PDF')

    # 4. Check reports archive list endpoint
    list_res = client.get('/api/v1/admin/reports/list', headers=headers)
    assert list_res.status_code == 200
    reports = list_res.get_json()['reports']
    assert len(reports) >= 1
    assert any(r['filename'] == pdf_filename for r in reports)

    # 5. Download latest PDF stream endpoint
    latest_res = client.get('/api/v1/admin/reports/download-latest-pdf', headers=headers)
    assert latest_res.status_code == 200
    assert latest_res.mimetype == 'application/pdf'
    assert latest_res.data.startswith(b'%PDF')

