class CognitoUser:
    """
    Holder class for authorizations.
    """
    
    def __init__(self, sub, email, name, is_admin, groups, db_handler, cognito_client):
        self.sub = sub
        self.email = email
        self.name = name
        self.is_admin = is_admin   
        self.groups = groups
        self.db_handler = db_handler
        self.cognito_client = cognito_client

    def get_colleagues(self):

        members = []
        print(self.groups)
        for group in self.groups:
            group_users_response = self.cognito_client.list_users_in_group(group)
            group_users = group_users_response.get("Users", [])
            print(group_users_response)
            for _user in group_users:
                members.append({
                    "sub": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "sub"), ""),
                    "email": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "email"), ""),
                    "name": next((user_attr["Value"] for user_attr in _user.get("Attributes", []) if user_attr["Name"] == "name"), ""),
                })

        return members
    
    def is_colleague(self, other_user_sub) -> bool:
        colleagues = self.get_colleagues()
        matching_colleague = next((colleague for colleague in colleagues if colleague["sub"] == other_user_sub), None)
        return True if matching_colleague is not None else False