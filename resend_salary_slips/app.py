import frappe
from frappe.query_builder.functions import Coalesce

@frappe.whitelist()
def email_salary_slips(payroll_entry_name, publish_progress=True):
    print('payroll_entry_name', payroll_entry_name)
    payroll_entry = frappe.get_doc("Payroll Entry", payroll_entry_name)
    salary_slips = get_sal_slip_list(payroll_entry, ss_status=1)

    if salary_slips:
        emailed_employees = []
        failed_employees = []
        
        for ss in salary_slips:
            queue_entries = frappe.get_all(
                    "Email Queue", 
                    filters={
                        "reference_name": ss.name,  # reference_name should match ss.name
                        "status": ["in", ["Sent", "Not Sent", "Sending"]]  # status must NOT be "Sent" or "Not Sent"
                    }
                )

            print('queue_entries', queue_entries, 'ss.name', ss.name)

            if not queue_entries:

                slip = frappe.get_doc("Salary Slip", ss.name)
                # Fetch employee's preferred email
                prefered_email = frappe.db.get_value("Employee", slip.employee, "prefered_email", cache=True)
                
                if prefered_email:
                    # If the employee has a preferred email, send the salary slip
                    slip.email_salary_slip()
                    emailed_employees.append(slip.employee_name)  # Add to the emailed list
                else:
                    # If no email is found, add to the failed list
                    failed_employees.append(slip.employee_name)  # Add to the failed list

        # After processing, print out the results

        if emailed_employees:        
            frappe.msgprint(f"Salary Slips emailed to: {', '.join(emailed_employees)}")
        if failed_employees:
            frappe.msgprint(f"Add a <strong>Prefered Email</strong> is for {', '.join(failed_employees)} and try again")

def get_sal_slip_list(pe, ss_status, as_dict=True):
    """
    Returns list of salary slips based on selected criteria
    """

    ss = frappe.qb.DocType("Salary Slip")
    ss_list = (
        frappe.qb.from_(ss)
        .select(ss.name, ss.salary_structure)
        .where(
            (ss.docstatus == ss_status)
            & (ss.start_date >= pe.start_date)
            & (ss.end_date <= pe.end_date)
            & (ss.payroll_entry == pe.name)
            & (Coalesce(ss.salary_slip_based_on_timesheet, 0) == pe.salary_slip_based_on_timesheet)
        )
    ).run(as_dict=as_dict)

    return ss_list