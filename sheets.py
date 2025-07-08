import gspread

class Sheets:
    def __init__(self):
        self.client = gspread.service_account(filename="credentials.json")
        self.sheet = self.client.open('example').sheet1

    def get_existing_rows(self):
        return self.sheet.get_all_values()

    def get_existing_urls(self):
        # TODO: Update the column index as needed
        column_index = 1  # 1-based index, e.g., 1 for column A
        urls = [row[column_index - 1] for row in self.get_existing_rows()[1:] if len(row) >= column_index]
        return urls

    def update_website_info(self, row_index, website_name, video_url):
        # Website name in column 2, video link in column 3
        self.sheet.update_cell(row_index, 2, website_name)
        self.sheet.update_cell(row_index, 3, video_url)

    def upload_to_drive(self, file_path):
        # TODO: Implement Google Drive upload logic
        # Return the public URL of the uploaded video
        raise NotImplementedError("Google Drive upload not implemented yet.")
        