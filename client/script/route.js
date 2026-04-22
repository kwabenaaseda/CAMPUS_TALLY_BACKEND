const API = {
    // AUTH
    user_signup:"/auth/signup",
    user_login:"/auth/login",

    // ADMIN
    admin_login:"/admin/login",
    admin_add_new:"/admin/add",
    admin_delete:"/admin/remove",

    // ELECTION
    admin_create_election:"/elections/create",
    admin_delete_election:(election_id)=>{
        return `/elections/delete/${election_id}` 
    },
    admin_get_elections:"/elections/all",
    admin_get_election:(election_id)=>{
        return `/elections/${election_id}`
    },
    admin_update_election: (election_id)=>{
        return `/elections/update/${election_id}`
    },
    
    // VOTES
    user_vote:"/votes/cast",
    user_get_vote_by_user:(user_id)=>{
        return `/votes/user/${user_id}`
    },
    all_get_votes_by_election:(election_id)=>{
        return `/votes/election/${election_id}`
    },
    
    // STATS
    all_get_stats:(election_id)=>{
        return `/stats/election/${election_id}`
    }
}

export default API